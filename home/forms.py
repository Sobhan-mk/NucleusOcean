from django import forms


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class ImageUploadForm(forms.Form):
    images = forms.ImageField(widget=MultiFileInput(attrs={'multiple': True}),
                             required=True)
