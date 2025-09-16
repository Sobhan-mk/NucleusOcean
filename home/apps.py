from django.apps import AppConfig
import os
from .hovernet_model import HoverNet
import torch


print('libraries imported')


class HomeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'home'

    def ready(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        state_dict_path = os.path.join(current_dir, 'hovernet.pth')

        self.hovernet = HoverNet()
        state_dict = torch.load(state_dict_path, map_location='cpu')
        self.hovernet.load_state_dict(state_dict)

        print('model loaded')

