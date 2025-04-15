from django.db import models
from django.conf import settings
from django.db.models import QuerySet
import uuid

class Tag(models.Model):
    tagname = models.CharField(max_length=256)
    namespace = models.CharField(max_length=256, blank=True)
    displayName = models.CharField(max_length=265, blank=True)

    description = models.TextField(blank=True)

    tag_count = models.IntegerField(default=0)

    # Forward reference to Media model fields
    creator_tags: "models.ManyToManyField[Tag, Media]"
    tags: "models.ManyToManyField[Tag, Media]"
    # Forward reference to discord model field
    assoc_discord: "models.Manager[DiscordCreator]"


    def count_uses(self):
        self.tag_count = self.tags.count() + self.creator_tags.count()
        discord_creator = self.assoc_discord.first()
        if discord_creator: 
            self.tag_count += discord_creator.count_uses()
        self.save()
        if(self.tag_count == 0):
            self.delete()


    @staticmethod
    def clear_orphans():
        counter = 0
        for tag in Tag.objects.filter(tags=None).filter(creator_tags=None).filter(assoc_discord=None):
            counter += 1
            tag.delete()
        print(f"Deleted {counter} orphaned tags")
    
    @staticmethod
    def count_tags():
        for tag in Tag.objects.all():
            precount = tag.tag_count
            tag.count_uses()
            postcount = tag.tag_count
            if postcount != precount:
                print(f'{tag.namespace}:{tag.tagname} | {precount} -> {postcount}')

    def __str__(self):
        return f'{self.namespace}:{self.tagname}'
    
    class Meta:
        ordering = ['namespace', 'tagname']

class DiscordCreator(models.Model):
    username = models.CharField(max_length=256)
    tag = models.ForeignKey(Tag, on_delete=models.SET_NULL, null=True, related_name='assoc_discord')

    # Forward reference to Media model field
    assoc_media: "models.Manager[Media]"

    def count_uses(self):
        uses = self.assoc_media.count()
        return uses

class Media(models.Model):
    file = models.FileField(default='default.jpg')
    creator_tags = models.ManyToManyField(Tag, blank=True, related_name='creator_tags')
    discord_creator = models.ForeignKey(DiscordCreator, on_delete=models.SET_NULL, null=True, related_name='assoc_media')
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

    @property
    def creators(self) -> list[Tag]:
        if self.discord_creator and self.discord_creator.tag:
            tags = list(self.creator_tags.all())
            tags.append(self.discord_creator.tag)
            return tags
        else:
            return list(self.creator_tags.all())

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
