import torch
from scipy.ndimage import label
from skimage.morphology import remove_small_objects
from skimage.feature import peak_local_max
from skimage.segmentation import watershed
import random
import numpy as np
import cv2
from torch.nn import functional as F


class PostProcess:
  def normalize(self, map):
    if isinstance(map, np.ndarray) :
      min = np.min(map)
      max = np.max(map)
    else:
      min = torch.min(map)
      max = torch.max(map)

    normalized_map = (map - min) / (max - min)
    return normalized_map

  def random_color_peak(self):
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

  def post_process(self, np_map, hv_map, tp_map):
    np_map = F.softmax(np_map, dim=0)

    foreground = np_map[0]
    foreground = (foreground > 0.5).int()

    foreground = foreground.detach().cpu().numpy()
    foreground = label(foreground)[0]
    foreground = remove_small_objects(foreground, min_size=25)
    foreground[foreground > 0] = 1

    h_map = hv_map[0].detach().cpu().numpy()
    v_map = hv_map[1].detach().cpu().numpy()

    h_map = self.normalize(h_map)
    v_map = self.normalize(v_map)

    h_grad_map = cv2.Sobel(h_map, cv2.CV_64F, 1, 0, ksize=21)
    v_grad_map = cv2.Sobel(v_map, cv2.CV_64F, 0, 1, ksize=21)

    h_grad_map = self.normalize(h_grad_map)
    v_grad_map = self.normalize(v_grad_map)

    overall = np.maximum(h_grad_map, v_grad_map)

    dist = (1 - overall) * foreground
    dist = -cv2.GaussianBlur(dist, (3, 3), 0)

    marker_coords = peak_local_max(-dist, min_distance=20)
    markers = np.zeros_like(dist)

    for idx, (x, y) in enumerate(marker_coords, start=1):
      markers[x, y] = idx

    dist = dist.astype(np.float32)
    markers = markers.astype(np.int32)
    foreground = foreground.astype(bool)

    instance_map = watershed(dist, markers=markers, mask=foreground)

    channels = tp_map.shape[0]
    tp_map = torch.argmax(tp_map, dim=0)
    tp_map = F.one_hot(tp_map, num_classes=channels)
    tp_map = tp_map.permute(2, 0, 1)

    tp_map = tp_map.detach().cpu().numpy()

    for channel_id in range(len(tp_map)):
      tp_map[channel_id] = tp_map[channel_id] * instance_map

    return dist, instance_map, tp_map


  def instance_seg_visualization(self, image, np_map, hv_map, tp_map):
    dist, instance_map, mask = self.post_process(np_map, hv_map, tp_map)

    colors = [
          (0,0,255),    # red
          (255,0,0),    # blue
          (0,255,0),    # green
          (0,255,255),  # yellow
          (255,0,255)   # purple
    ]

    instance_map_overlay = (self.normalize(image.permute(1, 2, 0)) * 255).detach().cpu().numpy().copy().astype(np.uint8)

    instance_ids = np.unique(instance_map)
    instance_ids = instance_ids[instance_ids != 0]

    for instance_id in instance_ids :
      instance_mask = (instance_map == instance_id).astype(np.uint8)

      contours, _ = cv2.findContours(instance_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
      cv2.drawContours(instance_map_overlay, contours,-1, color=self.random_color_peak(), thickness=2)

    type_overlay = (self.normalize(image.permute(1, 2, 0)) * 255).detach().cpu().numpy().copy().astype(np.uint8)


    for channel_id in range(len(mask) - 1):
      instance_ids = np.unique(mask[channel_id])
      instance_ids = instance_ids[instance_ids != 0]

      for instance_id in instance_ids:
        instance_mask = (mask[channel_id] == instance_id).astype(np.uint8)
        contours, _ = cv2.findContours(instance_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(type_overlay, contours, -1, color=colors[channel_id], thickness=2)

    return instance_map_overlay, type_overlay