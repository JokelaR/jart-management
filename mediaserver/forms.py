from django import forms
from .models import Media, EmbeddedMedia

class NewImageForm(forms.ModelForm):
    class Meta:
        model = Media
        fields = ['file', 'title', 'description', 'uploaderDescription', 'type', 'height', 'width', 'loop', 'uploader']

class NewMediaRemoteForm(forms.ModelForm):
    class Meta:
        model = Media
        fields = ['file', 'creator_tags', 'description', 'type', 'height', 'width', 'uploader']

class NewEmbedForm(forms.ModelForm):
    class Meta:
        model = EmbeddedMedia
        fields = ['url', 'title', 'description', 'uploaderDescription', 'type', 'height', 'width', 'loop', 'uploader']

class ImageMetadataForm(forms.Form):
    uuid = forms.UUIDField(required=True)
    title = forms.CharField(max_length=256, required=False)
    creator_tags = forms.CharField(required=False)
    tags = forms.CharField(required=False)
    description = forms.CharField(required=False)
    uploaderDescription = forms.CharField(required=False)
    loop = forms.BooleanField(required=False)