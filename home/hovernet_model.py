import torch
import torch.nn as nn
import torch.nn.functional as F


class ResidualUnit(torch.nn.Module):
  def __init__(self, in_channels, convs_outchannels, convs_kernelsizes, stride=1):
    super(ResidualUnit, self).__init__()
    self.stride = stride

    self.in_channels = in_channels
    self.out_channels = convs_outchannels[-1]

    self.bottleneck = nn.Sequential(
        nn.BatchNorm2d(in_channels),
        nn.ReLU(inplace=True),
        nn.Conv2d(in_channels,
                  convs_outchannels[0],
                  kernel_size=convs_kernelsizes[0],
                  stride=1,
                  padding=0,
                  bias=False),

        nn.BatchNorm2d(convs_outchannels[0]),
        nn.ReLU(inplace=True),
        nn.Conv2d(convs_outchannels[0],
                  convs_outchannels[1],
                  kernel_size=convs_kernelsizes[1],
                  stride=stride,
                  padding=1,
                  bias=False),

        nn.BatchNorm2d(convs_outchannels[1]),
        nn.ReLU(inplace=True),
        nn.Conv2d(convs_outchannels[1],
                  convs_outchannels[2],
                  kernel_size=convs_kernelsizes[2],
                  stride=1,
                  padding=0,
                  bias=False),
    )

    self.skip_projection = nn.Sequential(
        nn.Conv2d(self.in_channels,
                  self.out_channels,
                  kernel_size=1,
                  padding=0,
                  stride=stride,
                  bias=False),
        nn.BatchNorm2d(self.out_channels)
    )

  def forward(self, x):
    f_x = self.bottleneck(x)

    if self.stride != 1 or self.in_channels != self.out_channels :
      skip_x = self.skip_projection(x)
    else:
      skip_x = x
    output = f_x + skip_x

    return output


class ResidualBlock(torch.nn.Module):
  def __init__(self, in_channels, units_outchannels, units_kernelsizes, unit_counts, stride=1):
    super(ResidualBlock, self).__init__()

    self.stride = stride
    self.in_channels = in_channels
    self.out_channels = units_outchannels[-1]

    self.layers = nn.ModuleList()

    unit_in_channels = self.in_channels
    for unit in range(unit_counts):
      self.layers.append(
          ResidualUnit(unit_in_channels, units_outchannels, units_kernelsizes, stride=stride if unit == 0 else 1)
      )

      unit_in_channels = units_outchannels[-1]

    self.block = nn.Sequential(*self.layers)

  def forward(self, x):
    return self.block(x)


class HoverNetBackbone(torch.nn.Module):
  def __init__(self):
    super(HoverNetBackbone, self).__init__()

    self.stem = nn.Sequential(
        nn.Conv2d(3, 32, kernel_size=7, stride=1, padding=3, bias=False),
        nn.BatchNorm2d(32),
        nn.ReLU(inplace=True)
    )

    self.d0 = ResidualBlock(32, [32, 32, 128], [1, 3, 1], 2, stride=1)
    self.d1 = ResidualBlock(128, [64, 128, 256], [1, 3, 1], 3, stride=2)
    self.d2 = ResidualBlock(256, [128, 256, 512], [1, 3, 1], 4, stride=2)
    self.d3 = ResidualBlock(512, [256, 512, 1024], [1, 3, 1], 2, stride=2)

    self.bottleneck = nn.Conv2d(1024, 512, kernel_size=1, padding=0, stride=1, bias=False)

  def forward(self, x):

    x = self.stem(x)
    d0_output = self.d0(x)
    d1_output = self.d1(d0_output)
    d2_output = self.d2(d1_output)
    d3_output = self.d3(d2_output)
    bottleneck_output = self.bottleneck(d3_output)

    return d0_output, d1_output, d2_output, d3_output, bottleneck_output


class DenseUnit(torch.nn.Module):
  def __init__(self, in_channels, convs_outchannels, convs_kernelsizes):
    super(DenseUnit, self).__init__()

    self.dense_unit = nn.Sequential(
        nn.BatchNorm2d(in_channels),
        nn.ReLU(inplace=True),
        nn.Conv2d(
            in_channels,
            convs_outchannels[0],
            kernel_size = convs_kernelsizes[0],
            stride=1,
            padding=0,
            bias=False
        ),

        nn.BatchNorm2d(convs_outchannels[0]),
        nn.ReLU(inplace=True),
        nn.Conv2d(
            convs_outchannels[0],
            convs_outchannels[1],
            kernel_size = convs_kernelsizes[1],
            stride=1,
            padding=2,
            bias=False
        )
    )


  def forward(self, x):
    return self.dense_unit(x)


class DenseBlock(torch.nn.Module):
  def __init__(self, in_channels, units_outchannels, units_kernelsizes, unit_counts, stride=1):
    super(DenseBlock, self).__init__()

    self.stride = stride
    self.unit_counts = unit_counts

    self.before_conv = nn.Conv2d(in_channels,
                                 int(in_channels / 4),
                                 kernel_size=units_kernelsizes[1],
                                 stride=1,
                                 padding=2,
                                 bias=False)

    self.layers = nn.ModuleList()
    unit_in_channels = int(in_channels / 4)
    for unit in range(unit_counts):
      self.layers.append(DenseUnit(unit_in_channels, units_outchannels, units_kernelsizes))
      unit_in_channels += units_outchannels[-1]


    self.after_conv = nn.Conv2d(unit_in_channels,
                                unit_in_channels,
                                kernel_size=1,
                                padding=0,
                                stride=1,
                                bias=False)

  def forward(self, x, d):
    input = F.interpolate(x, scale_factor=2, mode='bilinear', align_corners=False)

    input = input + d

    unit_input = self.before_conv(input)
    for unit in self.layers :
      unit_input = torch.cat([unit_input, unit(unit_input)], dim=1)

    output = self.after_conv(unit_input)


    return output


class HoverNetDecoder(torch.nn.Module):
  def __init__(self, out_channels):
    super(HoverNetDecoder, self).__init__()

    self.u3 = DenseBlock(512, [128, 32], [1, 5], 4, 2)
    self.u2 = DenseBlock(int(4*32 + 512/4), [128, 32], [1, 5], 2, 2)
    self.u1 = DenseBlock(int(2*32 + 256/4), [128, 32], [1, 5], 1, 2)

    self.u0 = nn.Sequential(
        nn.BatchNorm2d(int(1*32 + 128/4)),
        nn.ReLU(inplace=True),
        nn.Conv2d(int(1*32 + 128/4),
                  out_channels,
                  kernel_size=1,
                  stride=1,
                  padding=0,
                  bias=False)
    )

  def forward(self, d0, d1, d2, d3, bottleneck):
    u3_output = self.u3(bottleneck, d2)
    u2_output = self.u2(u3_output, d1)
    u1_output = self.u1(u2_output, d0)

    final_output = self.u0(u1_output)

    return final_output


class HoverNet(torch.nn.Module):
  def __init__(self):
    super(HoverNet, self).__init__()

    self.backbone = HoverNetBackbone()
    self.decoder_np = HoverNetDecoder(2)
    self.decoder_hv = HoverNetDecoder(2)
    self.decoder_tp = HoverNetDecoder(6)

  def forward(self, x):
    d0, d1, d2, d3, bottleneck = self.backbone(x)
    np_output = self.decoder_np(d0, d1, d2, d3, bottleneck)
    hv_output = self.decoder_hv(d0, d1, d2, d3, bottleneck)
    tp_output = self.decoder_tp(d0, d1, d2, d3, bottleneck)
    return np_output, hv_output, tp_output
