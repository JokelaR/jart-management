from django.contrib.sites.models import Site
from django.http import HttpRequest
from .models import SiteSettings


def brand_context(request: HttpRequest):
    site = Site.objects.get_current()
    site_settings: SiteSettings = SiteSettings.load()

    if type(site_settings) != SiteSettings:
        raise Exception("Site settings not found for current site. Please create a SiteSettings object for the current site.")

    SITE_BRAND_NAME = site_settings.site_name
    SITE_BRAND_URL = site.domain
    SITE_BRAND_ICON = '' if not site_settings.site_brand_icon else site_settings.site_brand_icon.url
    SITE_BRAND_LOGO = '' if not site_settings.site_brand_logo else site_settings.site_brand_logo.url
    SITE_BRAND_DESC = site_settings.site_brand_description
    SITE_BRAND_EMBED = site_settings.site_brand_embed_description
    SITE_BRAND_PLEA = site_settings.site_brand_plea
    SITE_BRAND_COLOR = site_settings.site_brand_color

    return {
        'site_brand_name': SITE_BRAND_NAME,
        'site_brand_url': SITE_BRAND_URL,
        'site_brand_icon': SITE_BRAND_ICON,
        'site_brand_logo': SITE_BRAND_LOGO,
        'site_brand_desc': SITE_BRAND_DESC,
        'site_brand_embed': SITE_BRAND_EMBED,
        'site_brand_plea': SITE_BRAND_PLEA,
        'site_brand_color': SITE_BRAND_COLOR,
    }