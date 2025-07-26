from django.conf import settings

SITE_BRAND_NAME = settings.SITE_BRAND_NAME
SITE_BRAND_URL = settings.SITE_BRAND_URL
SITE_BRAND_ICON = settings.SITE_BRAND_ICON
SITE_BRAND_LOGO = settings.SITE_BRAND_LOGO
SITE_BRAND_DESC = settings.SITE_BRAND_DESC
SITE_BRAND_EMBED = settings.SITE_BRAND_EMBED
SITE_BRAND_PLEA = settings.SITE_BRAND_PLEA
SITE_BRAND_COLOR = settings.SITE_BRAND_COLOR

def brand_context(request):
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