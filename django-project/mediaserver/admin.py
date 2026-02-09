from django.contrib import admin
from .models import Media, Gallery, Tag

class OrphanTagFilter(admin.SimpleListFilter):
    title = 'Orphaned Tags'
    parameter_name = 'orphaned'

    def lookups(self, request, model_admin):
        return [
            ('yes', 'Orphan')
        ]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(tag_count=0)
        return queryset


class TagAdmin(admin.ModelAdmin):
    list_display = ['namespace', 'tagname', 'tag_count']
    list_filter = ['namespace', ('description', admin.EmptyFieldListFilter), OrphanTagFilter]
    search_fields = ['tagname', 'namespace']
    actions = ['check_tag_users']

    @admin.action(description='Check tag users')
    def check_tag_users(self, request, queryset):
        for tag in queryset:
            tag.count_uses()

# Register your models here.
admin.site.register(Media)
admin.site.register(Gallery)
admin.site.register(Tag, TagAdmin)