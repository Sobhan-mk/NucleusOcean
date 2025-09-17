from django.apps import AppConfig
import os
from .hovernet_model import HoverNet
import torch


print('libraries imported')


class HomeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'home'

    def ready(self):
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hovernet.pth')
        state_dict = torch.load(model_path, map_location='cpu')

        self.hovernet = HoverNet()

        self.hovernet.load_state_dict(state_dict)

        self.hovernet.eval()

