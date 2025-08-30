from django.urls import path, re_path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.index, name="index"),
    path("robots.txt", views.robots, name="robots.txt"),
    path("manage/gallery/<int:gallery_id>", views.edit_gallery, name="edit_gallery"),
    path("gallery/<int:gallery_id>", views.gallery, name="gallery"),
    path("galleries", views.galleries, name="galleries"),
    path("galleries/latest", views.latest_gallery, name="latest_gallery"),
    path("galleries/latest/<str:category>", views.latest_gallery_by_category, name="latest_gallery_by_category"),
    
    path("create/media", views.create_media, name="create_media"),
    path("create/media/tokenauth", views.create_media_with_token, name="create_media_with_token"),
    path("create/mediaEmbed", views.create_embedded_media, name="create_embedded_media"),
    path("create/gallery", views.create_gallery, name="create_gallery"),
    path("delete/gallery/<int:gallery_id>", views.delete_gallery, name="delete_gallery"),
    path("delete/media/<uuid:media_uuid>", views.delete_media, name="delete_media"),
    path("objects/orphaned", views.orphaned_media, name="orphaned_media"),
    path("objects/detach/<uuid:media_uuid>", views.detach_media, name="detach_media"),
    path("objects/<uuid:media_uuid>/gallery", views.get_media_gallery, name="get_media_gallery"),
    path("objects/gallery/<int:gallery_id>/media", views.get_gallery_media, name="get_gallery_media"),
    path("objects/gallery/<int:gallery_id>/metadata", views.get_gallery_metadata, name="get_gallery_metadata"),
    path("categories/json", views.get_categories, name="get_categories"),
    path("modify/media", views.modify_media, name="modify_media"),
    path("modify/gallery/<int:gallery_id>/media", views.update_gallery_media, name="update_gallery_media"),
    path("modify/gallery/<int:gallery_id>/title", views.update_gallery_title, name="update_gallery_title"),
    path("modify/gallery/<int:gallery_id>/visibility", views.update_gallery_visibility, name="update_gallery_visibility"),
    path("modify/gallery/<int:gallery_id>/date", views.update_gallery_date, name="update_gallery_date"),
    path("modify/gallery/<int:gallery_id>/category", views.update_gallery_category, name="update_gallery_category"),
    path("modify/gallery/<int:gallery_id>/associate_media", views.associate_media, name="associate_media"),
    path("modify/gallery/<int:gallery_id>/associate_single_media", views.add_single_media, name="add_single_media"),

    re_path(r'^creator/(?P<tag>.+?)$', views.CreatorTagListView.as_view(template_name="galleries/tag_list.html"), name="media_by_creator_tag"),
    re_path(r'^tags/(?P<namespace>\w+)/(?P<tag>.+?)$', views.TagListView.as_view(template_name="galleries/tag_list.html"), name="media_by_tag"),
    path("tags/", views.all_tags, name="all_tags"),
    path("tags/discordLink", views.set_discord_user_tag, name="set_discord_user_tag"),
    path("objects/discordUnlink", views.remove_discord_user, name="remove_discord_user"),

    path("tags/autocomplete/", views.tags_by_startswith, name="tags_by_startswith"),

    #override allauth non-login urls
    re_path(r'^accounts\/(password|confirm-email|email).*', views.redirect_home, name="index_redirect"),
    path("accounts/signup/", views.redirect_login, name="login_redirect"),
    path("accounts/login/", views.redirect_login, name="login_redirect"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)