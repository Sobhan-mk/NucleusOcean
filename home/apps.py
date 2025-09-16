from django.apps import AppConfig
import os
from .hovernet_model import HoverNet
import torch


print('libraries imported')


class HomeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'home'

    def ready(self):
        self.hovernet = HoverNet()

        print('model loaded')

