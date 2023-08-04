from django import forms
from .models import Media

class NewImageForm(forms.ModelForm):
    class Meta:
        model = Media
        fields = ['file', 'author', 'description', 'uploaderDescription', 'type', 'height', 'width', 'loop', 'uploader']

class ImageMetadataForm(forms.Form):
    uuid = forms.UUIDField(required=True)
    author = forms.CharField(max_length=256, required=False)
    description = forms.CharField(required=False)
    uploaderDescription = forms.CharField(required=False)
    loop = forms.BooleanField(required=False)