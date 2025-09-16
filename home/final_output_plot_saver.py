import matplotlib.pyplot as plt
from django.conf import settings
import os
import numpy as np
from uuid import uuid4


def plot_final_output(images, instance_maps, tp_maps):
    print(type(images))
    num_samples = images.shape[0]

    fig, axes = plt.subplots(num_samples, 3, figsize=(12, num_samples*4))
    axes = np.atleast_2d(axes)

    for idx in range(num_samples):
        image = images[idx]
        instance_map = instance_maps[idx]
        tp_map = tp_maps[idx]

        axes[idx][0].imshow(image.permute(1, 2, 0))
        axes[idx][0].set_title(f'image {idx+1}')
        axes[idx][0].axis('off')

        axes[idx][1].imshow(instance_map, cmap="tab20")
        axes[idx][1].set_title(f'instance map {idx+1}')
        axes[idx][1].axis('off')

        axes[idx][2].imshow(tp_map, cmap="viridis")
        axes[idx][2].set_title(f'tp map {idx+1}')
        axes[idx][2].axis('off')

    plt.tight_layout()

    file_path = os.path.join(settings.MEDIA_ROOT, 'output_images', f'{uuid4().hex}.png')
    file_url = f'{settings.MEDIA_URL}output_images/{os.path.basename(file_path)}'

    fig.savefig(file_path, dpi=300)
    plt.close(fig)

    return file_url
