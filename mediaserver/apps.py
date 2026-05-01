from django.apps import AppConfig
from django.conf import settings

def default_site_settings(sender: AppConfig, **kwargs: object) -> None:
    from django.contrib.sites.models import Site
    from .models import SiteSettings

    site, _ = Site.objects.get_or_create(id=settings.SITE_ID)
    SiteSettings.objects.get_or_create(site=site)

class MediaserverConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mediaserver'

    def ready(self):
        from django.db.models.signals import post_migrate
        post_migrate.connect(default_site_settings, sender=self, dispatch_uid='mediaserver.default_site_settings')