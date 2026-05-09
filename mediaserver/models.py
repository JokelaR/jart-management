from django.db import models
from django.conf import settings
from django.contrib.sites.models import Site
from easy_thumbnails.signals import saved_file # pyright: ignore[reportMissingTypeStubs]
from easy_thumbnails.signal_handlers import generate_aliases_global # pyright: ignore[reportMissingTypeStubs, reportUnknownVariableType]
import uuid

class SiteSettings(models.Model):
    site = models.OneToOneField(Site, related_name='settings', on_delete=models.CASCADE)
    site_name = models.CharField(max_length=256, default=settings.SITE_BRAND_NAME)
    site_brand_color = models.CharField(max_length=256, default=settings.SITE_BRAND_COLOR)
    site_brand_description = models.TextField(default=settings.SITE_BRAND_DESC)
    site_brand_embed_description = models.TextField(default=settings.SITE_BRAND_EMBED)
    site_brand_plea = models.TextField(default=settings.SITE_BRAND_PLEA)

    site_brand_icon = models.ImageField(upload_to='site/')
    site_brand_logo = models.ImageField(upload_to='site/')

    holiday_mode = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
    
    def delete(self, *args, **kwargs):
        pass

    class Meta:
        verbose_name_plural = "Site settings"

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
        if(self.tag_count <= 0):
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
    
saved_file.connect(generate_aliases_global) # pyright: ignore[reportUnknownArgumentType]

class Media(models.Model):
    file = models.FileField(default='default.jpg')
    creator_tags: models.ManyToManyField[Tag, Media] = models.ManyToManyField(Tag, blank=True, related_name='creator_tags')
    discord_creator: models.ForeignKey[DiscordCreator | None] = models.ForeignKey(DiscordCreator, on_delete=models.SET_NULL, null=True, related_name='assoc_media')
    title = models.CharField(max_length=256, blank=True)
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    uploaderDescription = models.TextField(blank=True)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=64)
    height = models.IntegerField(null=True)
    width = models.IntegerField(null=True)
    loop = models.BooleanField()
    tags: models.ManyToManyField[Tag, "Media"] = models.ManyToManyField(Tag, blank=True, related_name='tags')
    uploaded_date = models.DateTimeField("date uploaded", auto_now_add=True)

    # Forward reference to Gallery model field
    media_gallery: "models.ManyToManyField[Gallery, Media]"

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
    
    class Meta:
        verbose_name_plural = "Media"
    
class EmbeddedMedia(Media):
    url = models.URLField()
    def __str__(self):
        return f'{self.url} - {self.type} file by {self.creator_tags.first()}'

class Gallery(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=256)
    created_date = models.DateTimeField("date created", auto_now_add=True)
    media_items: models.ManyToManyField[Media, "Gallery"] = models.ManyToManyField(Media, through="GalleryOrder", related_name="media_gallery")
    category = models.CharField(max_length=64)
    visible = models.BooleanField(default=False)

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name_plural = "Galleries"
    
class GalleryOrder(models.Model):
    media =  models.ForeignKey(Media, on_delete=models.CASCADE)
    gallery = models.ForeignKey(Gallery, on_delete=models.CASCADE)
    order = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['media', 'gallery'], name="Every image has one gallery")
        ]
