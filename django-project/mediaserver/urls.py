from django.urls import path, re_path
from django.views.generic.base import RedirectView
from . import views
from allauth import urls

urlpatterns = [
    path("", views.index, name="index"),
    path("manage/gallery/<int:gallery_id>", views.edit_gallery, name="edit_gallery"),
    path("gallery/<int:gallery_id>", views.gallery, name="gallery"),
    path("galleries", views.galleries, name="galleries"),
    path("create/media", views.create_media, name="create_media"),
    path("create/gallery", views.create_gallery, name="create_gallery"),
    path("delete/gallery/<int:gallery_id>", views.delete_gallery, name="delete_gallery"),
    path("modify/media", views.modify_media, name="modify_media"),
    path("modify/gallery/<int:gallery_id>/media", views.update_gallery_media, name="update_gallery_media"),
    path("modify/gallery/<int:gallery_id>/title", views.update_gallery_title, name="update_gallery_title"),
    path("modify/gallery/<int:gallery_id>/associate_media", views.associate_media, name="associate_media"),
    #override allauth non-login urls
    re_path(r'^accounts\/(password|confirm-email|email).*', views.redirect_home, name="index_redirect"),
    path("accounts/login/", views.redirect_login, name="login_redirect")
]