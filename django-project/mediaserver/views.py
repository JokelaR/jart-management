from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_http_methods, require_safe
from django.http import HttpResponse, HttpResponseRedirect, Http404
from .models import Gallery, Media
from .forms import NewImageForm, ImageMetadataForm
from django.dispatch import receiver
from django.db.models.signals import post_delete
from django.urls import reverse
import os, json
# Create your views here.
@require_safe
def index(request):
    gallery_list = Gallery.objects.order_by('category', '-created_date')
    return render(request, "galleries/index.html", {'gallery_list': gallery_list})

@require_safe
def redirect_home(request, leftovers):
    return HttpResponseRedirect('/')

@require_safe
def redirect_login(request):
    return HttpResponseRedirect('/accounts/discord/login')

@require_safe
def galleries(request):
    gallery_list = Gallery.objects.order_by('category', '-created_date')
    print(gallery_list)
    return render(request, "galleries/index.html", {'gallery_list': gallery_list})

@require_safe
def gallery(request, gallery_id):
    gallery = get_object_or_404(Gallery, pk=gallery_id)
    items = gallery.media_items.order_by('galleryorder')
    return render(request, "galleries/gallery.html", {'gallery': gallery, 'items': items})

@require_safe
def latest_gallery(request):
    gallery = Gallery.objects.order_by('-created_date').first()
    if gallery is not None:
        return HttpResponseRedirect(reverse("gallery", kwargs={'gallery_id':gallery.id}))
    else:
        return HttpResponseRedirect('/')
    
def latest_gallery_by_category(request, category):
    gallery = Gallery.objects.filter(category__iexact=category).order_by('-created_date').first()
    if gallery is not None:
        return HttpResponseRedirect(reverse("gallery", kwargs={'gallery_id':gallery.id}))
    else:
        raise Http404(f'No galleries in "{category}"')
    

@require_safe
@login_required
@permission_required('mediaserver.change_gallery')
def edit_gallery(request, gallery_id):
    gallery = get_object_or_404(Gallery, pk=gallery_id)
    media_items = gallery.media_items.order_by('galleryorder')
    categories = Gallery.objects.all().distinct('category').values_list('category', flat=True)
    print(categories)
    return render(request, "galleries/manage_gallery.html", {'gallery': gallery, 'media_items': media_items, 'categories': categories})

@login_required
@require_http_methods(['POST'])
@permission_required('mediaserver.add_media')
def create_media(request):
    tempDict = request.POST.copy()
    tempDict['uploader'] = request.user
    form = NewImageForm(tempDict, request.FILES)
    if form.is_valid():
        created_media = form.save()
        response = {
            'url': created_media.file.name, 
            'uuid': created_media.uuid.hex
        }
        return HttpResponse(json.dumps(response))
    return HttpResponse(status=400)

@login_required
@require_http_methods(["DELETE", "POST"])
@permission_required('mediaserver.change_media')
def modify_media(request):
    if request.method == "POST":
        form = ImageMetadataForm(request.POST or None)
        if form.is_valid():
            updated_media = Media.objects.get(uuid=form.cleaned_data['uuid'])
            updated_media.author = form.cleaned_data['author']
            updated_media.description = form.cleaned_data['description']
            updated_media.uploaderDescription = form.cleaned_data['uploaderDescription']
            updated_media.loop = form.cleaned_data['loop']
            updated_media.save()
            return HttpResponse(f'Updated {updated_media}')
        else:
            return HttpResponse(status=400)
    elif request.method == "DELETE":
        if request.body:
            Media.objects.get(uuid=request.body.decode()).delete()
            return HttpResponse(f'Deleted {request.body}')
        else:
            return HttpResponse(status=400)
    else:
        return HttpResponse(status=400)

@login_required
@require_http_methods(["POST"])
@permission_required('mediaserver.change_gallery')
def update_gallery_media(request, gallery_id):
    gallery = Gallery.objects.get(id=gallery_id)
    gallery.media_items.clear()
    #expect data in the format 'uuid,uuid,uuid'
    i = 0
    for media_uuid in request.body.decode().split(','):
        gallery.media_items.add(Media.objects.get(uuid=media_uuid), through_defaults={'order': i})
    return HttpResponse(f'Updated pairs for Gallery #{gallery_id}')

    
@login_required
@require_http_methods(["POST"])
@permission_required('mediaserver.change_gallery')
def update_gallery_title(request, gallery_id):
    gallery = Gallery.objects.get(id=gallery_id)
    gallery.title = request.body.decode()
    gallery.save()
    return HttpResponse(f'Updated #{gallery_id} title')

@login_required
@require_http_methods(["POST"])
@permission_required('mediaserver.change_gallery')
def update_gallery_category(request, gallery_id):
    gallery = Gallery.objects.get(id=gallery_id)
    gallery.category = request.body.decode()
    gallery.save()
    return HttpResponse(f'Updated #{gallery_id} category')

@login_required
@require_http_methods(["POST"])
@permission_required('mediaserver.change_gallery')
def associate_media(request, gallery_id):
    #expect body in form of 'uuid,order'
    uuid, order = request.body.decode().split(',')
    gallery = Gallery.objects.get(id=gallery_id)
    media = Media.objects.get(uuid=uuid)
    gallery.media_items.add(media, through_defaults={'order': order})
    return HttpResponse(status=200)

@login_required
@require_http_methods(["POST"])
@permission_required('mediaserver.add_gallery')
def create_gallery(request):
    new_gallery = Gallery(title="New Gallery", category="other")
    new_gallery.save()
    return HttpResponseRedirect(reverse('edit_gallery', args=([new_gallery.id]))) # type: ignore
    
@login_required
@require_http_methods(["POST"])
@permission_required('mediaserver.change_gallery')
def delete_gallery(request, gallery_id):
    gallery = Gallery.objects.get(id=gallery_id)
    for media_item in gallery.media_items.all():
        media_item.delete()
    gallery.delete()
    return HttpResponseRedirect('/')

@receiver(post_delete, sender=Media)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `MediaFile` object is deleted.
    """
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)