from django.db import models
from django.conf import settings
import uuid, datetime

class Media(models.Model):
    file = models.FileField()
    author = models.CharField(max_length=256, blank=True)
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    uploaderDescription = models.TextField(blank=True)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=64)
    height = models.IntegerField(null=True)
    width = models.IntegerField(null=True)
    loop = models.BooleanField()
    def __str__(self):
        return f'{self.file.name} - {self.type} file by {self.author}'

class Gallery(models.Model):
    title = models.CharField(max_length=256)
    created_date = models.DateTimeField("date created", auto_now_add=True)
    media_items = models.ManyToManyField(Media, through="GalleryOrder")
    def __str__(self):
        return self.title
    
class GalleryOrder(models.Model):
    media =  models.ForeignKey(Media, on_delete=models.CASCADE)
    gallery = models.ForeignKey(Gallery, on_delete=models.CASCADE)
    order = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['media', 'gallery'], name="Every image has one gallery")
        ]
