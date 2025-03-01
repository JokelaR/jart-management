from django.urls import path, re_path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.index, name="index"),
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
    path("media/orphaned", views.orphaned_media, name="orphaned_media"),
    path("modify/media", views.modify_media, name="modify_media"),
    path("modify/gallery/<int:gallery_id>/media", views.update_gallery_media, name="update_gallery_media"),
    path("modify/gallery/<int:gallery_id>/title", views.update_gallery_title, name="update_gallery_title"),
    path("modify/gallery/<int:gallery_id>/visibility", views.update_gallery_visibility, name="update_gallery_visibility"),
    path("modify/gallery/<int:gallery_id>/date", views.update_gallery_date, name="update_gallery_date"),
    path("modify/gallery/<int:gallery_id>/category", views.update_gallery_category, name="update_gallery_category"),
    path("modify/gallery/<int:gallery_id>/associate_media", views.associate_media, name="associate_media"),

    path("creator/<str:tag>", views.CreatorTagListView.as_view(template_name="galleries/tag_list.html"), name="media_by_creator_tag"),
    path("tags/<str:namespace>/<str:tag>", views.TagListView.as_view(template_name="galleries/tag_list.html"), name="media_by_tag"),
    path("tags/", views.all_tags, name="all_tags"),

    path("tags/autocomplete/", views.tags_by_startswith, name="tags_by_startswith"),

    #override allauth non-login urls
    re_path(r'^accounts\/(password|confirm-email|email).*', views.redirect_home, name="index_redirect"),
    path("accounts/signup/", views.redirect_login, name="login_redirect"),
    path("accounts/login/", views.redirect_login, name="login_redirect"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)