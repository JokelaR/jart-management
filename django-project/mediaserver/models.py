from django.db import models
from django.conf import settings
import uuid

class Tag(models.Model):
    tagname = models.CharField(max_length=256)
    namespace = models.CharField(max_length=256, blank=True)
    displayName = models.CharField(max_length=265, blank=True)

    description = models.TextField(blank=True)

    tag_count = models.IntegerField(default=0)

    def count_uses(self):
        self.tag_count = self.tags.count() + self.creator_tags.count()
        print(f'{self.namespace}:{self.tagname}, {self.tag_count} instances')
        self.save()
        if(self.tag_count == 0):
            self.delete()

    # Forward reference to Media model fields
    creator_tags: "models.ManyToManyField"
    tags: "models.ManyToManyField"

    @staticmethod
    def clear_orphans():
        counter = 0
        for tag in Tag.objects.filter(tags=None).filter(creator_tags=None):
            counter += 1
            tag.delete()
        print(f"Deleted {counter} orphaned tags")
    
    @staticmethod
    def count_tags():
        for tag in Tag.objects.all():
            tag.count_uses()

    def __str__(self):
        return f'{self.namespace}:{self.tagname}'
    
    class Meta:
        ordering = ['namespace', 'tagname']

class Media(models.Model):
    file = models.FileField(default='default.jpg')
    creator_tags = models.ManyToManyField(Tag, blank=True, related_name='creator_tags')
    title = models.CharField(max_length=256, blank=True)
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    uploaderDescription = models.TextField(blank=True)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=64)
    height = models.IntegerField(null=True)
    width = models.IntegerField(null=True)
    loop = models.BooleanField()
    tags = models.ManyToManyField(Tag, blank=True, related_name='tags')
    uploaded_date = models.DateTimeField("date uploaded", auto_now_add=True)

    def __str__(self):
        return f'{self.file.name} - {self.type} file by {self.creator_tags.first()}'
    
class EmbeddedMedia(Media):
    url = models.URLField()
    def __str__(self):
        return f'{self.url} - {self.type} file by {self.creator_tags.first()}'

class Gallery(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=256)
    created_date = models.DateTimeField("date created", auto_now_add=True)
    media_items = models.ManyToManyField(Media, through="GalleryOrder", related_name="media_gallery")
    category = models.CharField(max_length=64)
    visible = models.BooleanField(default=False)

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
