from typing import Any

from django.contrib import admin
from django.template.response import TemplateResponse
from .models import Media, Gallery, SiteSettings, Tag
from django.http import HttpRequest
from django.db.models import QuerySet


class SiteSettingsAdmin(admin.ModelAdmin):
    exclude = ['site']
    
    def changeform_view(self, request: HttpRequest, object_id: str | None = ..., form_url: str = ..., extra_context: dict[str, bool] | None = ...) -> TemplateResponse:
        extra_context = extra_context or {}
        extra_context['show_delete'] = False
        extra_context['show_save_and_add_another'] = False
        extra_context['show_save_and_continue'] = False

        return super().changeform_view(request, object_id, form_url, extra_context)

    def has_delete_permission(self, request: HttpRequest, obj: Any | None = ...) -> bool:
        return False


class OrphanTagFilter(admin.SimpleListFilter):
    title = 'Orphaned Tags'
    parameter_name = 'orphaned'

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin):
        return [
            ('yes', 'Orphan')
        ]

    def queryset(self, request: HttpRequest, queryset: QuerySet[Tag]):
        if self.value() == 'yes':
            return queryset.filter(tag_count=0)
        return queryset


class TagAdmin(admin.ModelAdmin):
    list_display = ['namespace', 'tagname', 'tag_count']
    list_filter = ['namespace', ('description', admin.EmptyFieldListFilter), OrphanTagFilter]
    search_fields = ['tagname', 'namespace']
    actions = ['check_tag_users']

    def get_actions(self, request: HttpRequest):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    @admin.action(description='Check tag users')
    def check_tag_users(self, request: HttpRequest, queryset: QuerySet[Tag]):
        for tag in queryset:
            tag.count_uses()

# Register your models here.
admin.site.register(Media)
admin.site.register(Gallery)
admin.site.register(Tag, TagAdmin)
admin.site.register(SiteSettings, SiteSettingsAdmin)