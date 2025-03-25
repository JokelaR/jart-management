from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_http_methods, require_safe
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.list import ListView
from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseRedirect, Http404
from .models import *
from .forms import *
from jartmanagement.settings import REMOTE_USERNAME, REMOTE_TOKEN
from django.dispatch import receiver
from django.db.models.signals import post_delete
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
import os, json
from datetime import datetime
# Create your views here.


TOKEN_UPLOAD_USER = get_user_model().objects.get(username=REMOTE_USERNAME)

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
    return render(request, "galleries/index.html", {'gallery_list': gallery_list})

@require_safe
def gallery(request, gallery_id):
    gallery = get_object_or_404(Gallery, pk=gallery_id)
    items = gallery.media_items.order_by('galleryorder')
    return render(request, "galleries/gallery.html", {'gallery': gallery, 'page_obj': items})

@require_safe
def latest_gallery(request):
    gallery = Gallery.objects.filter(visible=True).order_by('-created_date').first()
    if gallery is not None:
        return HttpResponseRedirect(reverse("gallery", kwargs={'gallery_id':gallery.id}))
    else:
        return HttpResponseRedirect('/')

@require_safe
def all_tags(request):
    tags = Tag.objects.all()
    return render(request, "tags.html", {'tags': tags})
    
def latest_gallery_by_category(request, category):
    gallery = Gallery.objects.filter(category__iexact=category, visible=True).order_by('-created_date').first()
    if gallery is not None:
        return HttpResponseRedirect(reverse("gallery", kwargs={'gallery_id':gallery.id}))
    else:
        raise Http404(f'No galleries in "{category}"')
        
def tag_list_by_namespace(request, namespace):
    tags = Tag.objects.filter(namespace__iexact=namespace)
    return JsonResponse([tag.tagname for tag in tags])

@require_http_methods(['POST'])
@permission_required('mediaserver.change_media')
def tags_by_startswith(request):
    data = json.loads(request.body.decode())
    if data['namespace'] == "":
        tags = Tag.objects.order_by('tag_count').filter(tagname__istartswith=data['incomplete_tag']).reverse()[:10]
    else:
        tags = Tag.objects.order_by('tag_count').filter(namespace__iexact=data['namespace'], tagname__istartswith=data['incomplete_tag']).reverse()[:10]
    return JsonResponse({'tags': [{'namespace': tag.namespace, 'tagname': tag.tagname} for tag in tags]}, safe=False)

@login_required
@permission_required('mediaserver.delete_tag')
@require_http_methods(['POST'])
def delete_tag(tag):
    tag = Tag.objects.get(tagname=tag)
    tag.delete()
    return HttpResponse(status=200)

@login_required
@permission_required('mediaserver.change_media')
@require_http_methods(['POST'])
def add_tag(media_uuid, tag):
    media = Media.objects.get(uuid=media_uuid)
    tag = Tag.objects.get(tagname=tag)
    media.tags.add(tag)
    return HttpResponse(status=200)

@login_required
@permission_required('mediaserver.change_media')
@require_http_methods(['POST'])
def remove_tag(media_uuid, tag):
    media = Media.objects.get(uuid=media_uuid)
    tag = Tag.objects.get(tagname=tag)
    media.tags.remove(tag)
    return HttpResponse(status=200)

@require_safe
@login_required
@permission_required('mediaserver.change_gallery')
def edit_gallery(request, gallery_id):
    gallery = get_object_or_404(Gallery, pk=gallery_id)
    media_items = gallery.media_items.order_by('galleryorder')
    categories = Gallery.objects.all().distinct('category').values_list('category', flat=True)
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

@csrf_exempt
@require_http_methods(['POST'])
def create_media_with_token(request):
    token = request.POST.get('token')
    if not token or token == '' or token != REMOTE_TOKEN:
        return JsonResponse({'error': 'Token validation failed'}, status=401)
    request_data = request.POST.copy()
    
    # Mandatory fields
    try:
        file = request.FILES["file"]
    except KeyError:
        return JsonResponse({'error': 'Missing file'}, status=400)
    creator_name = request.POST.get('creator')
    type = request.POST.get('type')
    height = request.POST.get('height')
    width = request.POST.get('width')
    if not creator_name or not type or not height or not width:
        return JsonResponse({'error': 'Missing one or more mandatory field'}, status=400)

    
    # Optional fields
    try:
        description = request_data['description']
    except KeyError:
        description = ''

    creator = None
    try:
        creator = Tag.objects.get(namespace='creator', displayName=creator_name)
    except ObjectDoesNotExist:
        description = f'❗Unlinked creator "{creator_name}"❗ - {description}'
    
    media = Media(file=file, description=description, type=type, height=height, width=width, loop=False, uploader=TOKEN_UPLOAD_USER)
    if creator:
        media.creator_tags.add(creator)
    media.save()
    return JsonResponse({'created_uuid': media.uuid}, status=200)

@require_safe
@require_http_methods(['GET'])
def get_media_gallery(request, media_uuid):
    media = get_object_or_404(Media, uuid=media_uuid)
    gallery = media.media_gallery.first() # type: ignore
    if gallery:
        return JsonResponse({'gallery_id': gallery.id}, status=200)
    return JsonResponse({'error': 'No gallery'}, status=404)

@login_required
@require_http_methods(['POST'])
@permission_required('mediaserver.add_media')
def create_embedded_media(request):
    tempDict = request.POST.copy()
    tempDict['uploader'] = request.user
    form = NewEmbedForm(tempDict)
    if form.is_valid():
        created_media = form.save()
        response = {
            'url': created_media.url, 
            'uuid': created_media.uuid.hex
        }
        return HttpResponse(json.dumps(response))
    return HttpResponse(status=400)

@login_required
@require_http_methods(["DELETE", "POST"])
@permission_required('mediaserver.change_media')
def modify_media(request: HttpRequest):
    if request.method == "POST":
        form = ImageMetadataForm(request.POST or None)
        if form.is_valid():
            updated_media = Media.objects.get(uuid=form.cleaned_data['uuid'])
            updated_media.title = form.cleaned_data['title']
            updated_media.description = form.cleaned_data['description']
            updated_media.uploaderDescription = form.cleaned_data['uploaderDescription']
            updated_media.loop = form.cleaned_data['loop']

            current_creator_tags = [{'namespace': 'creator', 'tagname': tag.tagname} for tag in updated_media.creator_tags.all()]
            current_tags = [{'namespace': tag.namespace, 'tagname': tag.tagname} for tag in updated_media.tags.all()]

            #clear and re-add tags
            new_creator_tags = json.loads(form.cleaned_data['creator_tags'])
            new_tags = json.loads(form.cleaned_data['tags'])

            diff_creator_tags(updated_media, current_creator_tags, new_creator_tags)
            diff_tags(updated_media, current_tags, new_tags)

            updated_media.save()
            return HttpResponse(f'Updated {updated_media}')
        else:
            return HttpResponse(status=400)
    elif request.method == "DELETE":
        if request.body:
            media = Media.objects.get(uuid=request.body.decode())
            for tag in media.tags.all():
                media.tags.remove(tag)
                tag.count_tags()
            media.delete()
            return HttpResponse(f'Deleted {request.body}')
        else:
            return HttpResponse(status=400)
    else:
        return HttpResponse(status=400)
    
def diff_tags(media: Media, current_tags: list[dict[str, str]], new_tags: list[dict[str, str]]):
    if(current_tags != new_tags):
        for tag in current_tags:
            if tag not in new_tags:
                removed_tag = media.tags.get(namespace=tag['namespace'], tagname=tag['tagname'])
                media.tags.remove(removed_tag)
                print(f'removed {removed_tag} from {media}')
                removed_tag.count_tags()

        for tag in new_tags:
            if tag not in current_tags:
                try:
                    added_tag = Tag.objects.get(namespace=tag['namespace'], tagname=tag['tagname'])
                except ObjectDoesNotExist:
                    added_tag = Tag.objects.create(namespace=tag['namespace'], tagname=tag['tagname'])
                media.tags.add(added_tag)
                print(f'added {added_tag} to {media}')
                added_tag.count_uses()

def diff_creator_tags(media: Media, current_tags: list[dict[str, str]], new_tags: list[dict[str, str]]):
    if(current_tags != new_tags):
        for tag in current_tags:
            if tag not in new_tags:
                removed_tag = media.creator_tags.get(tagname=tag['tagname'])
                media.creator_tags.remove(removed_tag)
                print(f'removed {removed_tag} from {media}')
                removed_tag.count_tags()

        for tag in new_tags:
            if tag not in current_tags:
                try:
                    added_tag = Tag.objects.get(namespace='creator', tagname=tag['tagname'])
                except ObjectDoesNotExist:
                    added_tag = Tag.objects.create(namespace='creator', tagname=tag['tagname'])
                media.creator_tags.add(added_tag)
                print(f'added {added_tag} to {media}')
                added_tag.count_uses()

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
    return HttpResponse(f'{gallery.title}')

@login_required
@require_http_methods(["POST"])
@permission_required('mediaserver.change_gallery')
def update_gallery_visibility(request, gallery_id):
    gallery = Gallery.objects.get(id=gallery_id)
    gallery.visible = not gallery.visible
    gallery.save()
    return HttpResponse(f'{gallery.visible}')

@login_required
@require_http_methods(["POST"])
@permission_required('mediaserver.change_gallery')
def update_gallery_date(request, gallery_id):
    gallery = Gallery.objects.get(id=gallery_id)
    gallery.created_date = datetime.fromisoformat(f'{request.body.decode()}T00:00:00Z')
    gallery.save()
    return HttpResponse(f'{gallery.created_date}')

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
@permission_required('mediaserver.change_gallery')
def add_single_media(request, gallery_id):
    media = Media.objects.get(uuid=request.body.decode())
    gallery = Gallery.objects.get(id=gallery_id)
    gallery.media_items.add(media, through_defaults={'order': gallery.media_items.count()})
    return HttpResponse(status=200)

@login_required
@require_http_methods(["POST"])
@permission_required('mediaserver.add_gallery')
def create_gallery(request):
    new_gallery = Gallery(title="New Gallery", category="other")
    new_gallery.save()
    return HttpResponseRedirect(reverse('edit_gallery', args=([new_gallery.id])))
    
@login_required
@require_http_methods(["POST"])
@permission_required('mediaserver.delete_gallery')
def delete_gallery(request, gallery_id):
    gallery = Gallery.objects.get(id=gallery_id)
    for media_item in gallery.media_items.all():
        media_item.delete()
    gallery.delete()
    return HttpResponseRedirect('/')

@login_required
@require_http_methods(["POST"])
@permission_required('mediaserver.delete_gallery')
def delete_media(request, media_uuid):
    media = Media.objects.get(uuid=media_uuid)
    media.delete()
    return HttpResponseRedirect(reverse('orphaned_media'))

@login_required
@require_http_methods(["POST"])
@permission_required('mediaserver.change_media')
def detach_media(request, media_uuid):
    media = Media.objects.get(uuid=media_uuid)
    media.media_gallery.clear() # type: ignore
    return HttpResponseRedirect(reverse('orphaned_media'))

@login_required
@permission_required('mediaserver.change_gallery')
def orphaned_media(request):
    orphaned_media = Media.objects.filter(media_gallery=None).order_by('uploaded_date')
    galleries = Gallery.objects.all().values('id', 'title').order_by('category', '-created_date')
    return render(request, "galleries/orphaned_media.html", {'orphaned_media': orphaned_media, 'galleries': galleries})

@receiver(post_delete, sender=Media)
def auto_delete_file_on_delete(sender, instance: Media, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `MediaFile` object is deleted.
    """
    for tag in instance.tags.all():
        instance.tags.remove(tag)
        print(f'removed {tag} while deleting {instance}')
        tag.count_tags()
    
    for tag in instance.creator_tags.all():
        instance.creator_tags.remove(tag)
        print(f'removed {tag} while deleting {instance}')
        tag.count_tags()

    if instance.file and instance.type != 'embed':
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)


class CreatorTagListView(ListView):
    model = Media
    paginate_by = 10
    allow_empty = False

    def get_queryset(self):
        key = self.kwargs.get('tag', '')
        queryset = Media.objects.filter(creator_tags__tagname__iexact=key).order_by('uploaded_date').distinct().reverse()
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = Tag.objects.get(namespace='creator', tagname=self.kwargs.get('tag'))
        return context
    
class TagListView(ListView):
    model = Media
    paginate_by = 10
    allow_empty = False

    def get_queryset(self):
        tag = self.kwargs.get('tag', '')
        namespace = self.kwargs.get('namespace', '')
        
        if namespace == 'all':
            queryset = Media.objects.filter(tags__tagname__iexact=tag).order_by('uploaded_date').distinct().reverse()
        else:
            queryset = Media.objects.filter(tags__namespace__iexact=namespace, tags__tagname__iexact=tag).order_by('uploaded_date').distinct().reverse()
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.kwargs.get('namespace') == 'all':
            context['tag'] = Tag.objects.get(tagname=self.kwargs.get('tag'))
        else:
            context['tag'] = Tag.objects.get(namespace=self.kwargs.get('namespace'), tagname=self.kwargs.get('tag'))
        return context