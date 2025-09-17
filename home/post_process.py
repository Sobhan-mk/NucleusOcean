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
    foreground = self.normalize(foreground)
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

    instance_ids = np.unique(instance_map)
    instance_ids = instance_ids[instance_ids != 0]

    tp_map = F.softmax(tp_map[:-1], dim=0)
    type_map = np.zeros_like(instance_map)

    for instance_id in instance_ids:
        x_coords, y_coords = np.where(instance_map == instance_id)

        masked_probs = tp_map[:, x_coords, y_coords]
        average_probs = masked_probs.mean(dim=1)
        type_map[x_coords, y_coords] = torch.argmax(average_probs) + 1

    return instance_map, type_map

  def instance_seg_visualization(self, image, np_map, hv_map, tp_map):
    instance_map, type_map = self.post_process(np_map, hv_map, tp_map)

    nucleus_total_num = 0
    nucleus_type_num = [0, 0, 0, 0, 0]

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

    nucleus_total_num = len(instance_ids)

    for instance_id in instance_ids :
      instance_mask = (instance_map == instance_id).astype(np.uint8)

      contours, _ = cv2.findContours(instance_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
      cv2.drawContours(instance_map_overlay, contours,-1, color=self.random_color_peak(), thickness=2)

    type_overlay = (self.normalize(image.permute(1, 2, 0)) * 255).detach().cpu().numpy().copy().astype(np.uint8)

    instance_ids = np.unique(type_map)
    instance_ids = instance_ids[instance_ids != 0]

    for instance_id in instance_ids:
      type_mask = (type_map == instance_id).astype(np.uint8)

      contours, _ = cv2.findContours(type_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
      cv2.drawContours(type_overlay, contours,-1, color=colors[instance_id-1], thickness=2)

      type_insntace_ids = np.unique(instance_map * type_mask)
      nucleus_type_num[instance_id-1] = len(type_insntace_ids) - 1

    return instance_map_overlay, type_overlay, nucleus_total_num, nucleus_type_num