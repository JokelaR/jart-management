from .models import Media, Gallery, Tag

from django.contrib.sitemaps import GenericSitemap

sitemaps = {
    'media': GenericSitemap({
        'queryset': Media.objects.all(), 
        'date_field': 'last_updated'
    },
    priority=0.5),
    'galleries': GenericSitemap({
        'queryset': Gallery.objects.filter(visible=True), 
        'date_field': 'last_updated'}, 
    priority=0.7),
    'tags': GenericSitemap({
        'queryset': Tag.objects.filter(tag_count__gt=0),
        'date_field': 'last_updated'}, 
    priority=0.3)
}
