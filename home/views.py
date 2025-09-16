import torch
from django.shortcuts import render
from .forms import ImageUploadForm
from torchvision import transforms
from django.apps import apps
from .post_process import PostProcess
from .final_output_plot_saver import plot_final_output
from PIL import Image


def home(request):
    file_url = None

    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)

        print('form got')

        print(request.FILES)

        batch_input_data = []
        batch_instance_map = []
        batch_tp_map = []

        hovernet = apps.get_app_config('home').hovernet

        print('model implemented')

        transformer = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor()
        ])

        post_proc = PostProcess()

        images = request.FILES.getlist('images')

        for image in images:
            image = Image.open(image).convert('RGB')
            image = transformer(image)

            batch_input_data.append(image)

        batch_input_data = torch.stack(batch_input_data)

        print('input batch created')

        hovernet.eval()
        with torch.no_grad():
            np_maps, hv_maps, tp_maps = hovernet(batch_input_data)

        print('forward pass done')

        for image, np_map, hv_map, tp_map in zip(batch_input_data, np_maps, hv_maps, tp_maps):
            instance_output, tp_output = post_proc.instance_seg_visualization(image, np_map, hv_map, tp_map)

            batch_instance_map.append(torch.from_numpy(instance_output))
            batch_tp_map.append(torch.from_numpy(tp_output))

        batch_instance_map = torch.stack(batch_instance_map)
        batch_tp_map = torch.stack(batch_tp_map)

        print('post process done')

        file_url = plot_final_output(batch_input_data, batch_instance_map, batch_tp_map)

        print('plot saved')

    else:
        form = ImageUploadForm()

    context = {'form': form, 'file_url': file_url}

    return render(request, 'home/home.html', context)


def about_developer(request):
    return render(request, 'home/about_developer.html')
