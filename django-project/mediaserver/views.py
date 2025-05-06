from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import get_user_model, get_user
from django.contrib.auth.models import AnonymousUser
from django.views.decorators.http import require_http_methods, require_safe
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.list import ListView
from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseRedirect, Http404
from .models import *
from .forms import *
from jartmanagement.settings import REMOTE_USERNAME, REMOTE_TOKEN
from django.dispatch import receiver
from django.db.models.signals import post_delete
from django.db.models import Q
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
import os, json
from datetime import datetime

from typing import Any
from django.http import HttpRequest
from uuid import UUID

# Create your views here.


TOKEN_UPLOAD_USER = get_user_model().objects.get(username=REMOTE_USERNAME)

@require_safe
def index(request: HttpRequest):
    gallery_list = Gallery.objects.order_by('category', '-created_date')
    return render(request, "galleries/index.html", {'gallery_list': gallery_list})

@require_safe
def robots(request: HttpRequest):
    return render(request, "robots.txt", content_type="text/plain")

@require_safe
def redirect_home(request: HttpRequest, _: Any):
    return HttpResponseRedirect('/')

@require_safe
def redirect_login(request: HttpRequest):
    return HttpResponseRedirect('/accounts/discord/login')

@require_safe
def galleries(request: HttpRequest):
    gallery_list = Gallery.objects.order_by('category', '-created_date')
    return render(request, "galleries/index.html", {'gallery_list': gallery_list})

@require_safe
def gallery(request: HttpRequest, gallery_id: int):
    gallery = get_object_or_404(Gallery, pk=gallery_id)
    if not gallery.visible:
        user = get_user(request)
        if not user.has_perm('mediaserver.change_gallery'):
            raise Http404(f'Gallery {gallery_id} is not public yet')
    items = gallery.media_items.order_by('galleryorder')
    return render(request, "galleries/gallery.html", {'gallery': gallery, 'page_obj': items})

@require_safe
def latest_gallery(request: HttpRequest):
    gallery = Gallery.objects.filter(visible=True).order_by('-created_date').first()
    if gallery is not None:
        return HttpResponseRedirect(reverse("gallery", kwargs={'gallery_id':gallery.id}))
    else:
        return HttpResponseRedirect('/')

@require_safe
def all_tags(request: HttpRequest):
    tags = Tag.objects.all()
    return render(request, "tags.html", {'tags': tags})
    
def latest_gallery_by_category(request: HttpRequest, category: str):
    gallery = Gallery.objects.filter(category__iexact=category, visible=True).order_by('-created_date').first()
    if gallery is not None:
        return HttpResponseRedirect(reverse("gallery", kwargs={'gallery_id':gallery.id}))
    else:
        raise Http404(f'No galleries in "{category}"')
        
def tag_list_by_namespace(request: HttpRequest, namespace: str):
    tags = Tag.objects.filter(namespace__iexact=namespace)
    return JsonResponse([tag.tagname for tag in tags])

@require_http_methods(['POST'])
@permission_required('mediaserver.change_media')
def tags_by_startswith(request: HttpRequest):
    data = json.loads(request.body.decode())
    if data['namespace'] == "":
        tags = Tag.objects.order_by('tag_count').filter(tagname__istartswith=data['incomplete_tag']).reverse()[:10]
    else:
        tags = Tag.objects.order_by('tag_count').filter(namespace__iexact=data['namespace'], tagname__istartswith=data['incomplete_tag']).reverse()[:10]
    return JsonResponse({'tags': [{'namespace': tag.namespace, 'tagname': tag.tagname} for tag in tags]}, safe=False)

@login_required
@permission_required('mediaserver.delete_tag')
@require_http_methods(['POST'])
def delete_tag(tag: str):
    tag_o = Tag.objects.get(tagname=tag)
    tag_o.delete()
    return HttpResponse(status=200)

@login_required
@permission_required('mediaserver.change_media')
@require_http_methods(['POST'])
def add_tag(media_uuid: UUID, tag: str):
    media = Media.objects.get(uuid=media_uuid)
    tag_o = Tag.objects.get(tagname=tag)
    media.tags.add(tag_o)
    return HttpResponse(status=200)

@login_required
@permission_required('mediaserver.change_media')
@require_http_methods(['POST'])
def remove_tag(media_uuid: UUID, tag: str):
    media = Media.objects.get(uuid=media_uuid)
    tag_o = Tag.objects.get(tagname=tag)
    media.tags.remove(tag_o)
    return HttpResponse(status=200)

@require_safe
@login_required
@permission_required('mediaserver.change_gallery')
def edit_gallery(request: HttpRequest, gallery_id: int):
    gallery = get_object_or_404(Gallery, pk=gallery_id)
    return render(request, "galleries/manage_gallery.html", {'gallery': gallery})

@login_required
@require_http_methods(['POST'])
@permission_required('mediaserver.add_media')
def create_media(request: HttpRequest):
    tempDict = request.POST.copy()
    tempDict['uploader'] = request.user # type: ignore
    form = NewImageForm(tempDict, request.FILES)
    if form.is_valid():
        created_media = form.save()
        response = {
            'url': '/media/' + created_media.file.name, 
            'uuid': created_media.uuid.hex
        }
        return HttpResponse(json.dumps(response))
    return HttpResponse(status=400)

@csrf_exempt
@require_http_methods(['POST'])
def create_media_with_token(request: HttpRequest):
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

    creator_object, _ = DiscordCreator.objects.get_or_create(username=creator_name)
    
    media = Media(file=file, discord_creator=creator_object, description=description, type=type, height=height, width=width, loop=False, uploader=TOKEN_UPLOAD_USER)
    media.save()
    if creator_object.tag:
        creator_object.tag.count_uses()
    return JsonResponse({'created_uuid': media.uuid}, status=200)

@require_safe
@require_http_methods(['GET'])
def get_media_gallery(request: HttpRequest, media_uuid: UUID):
    media = get_object_or_404(Media, uuid=media_uuid)
    gallery: Gallery = media.media_gallery.first() # type: ignore
    if gallery:
        return JsonResponse({'gallery_id': gallery.id}, status=200)
    return JsonResponse({'error': 'No gallery'}, status=404)

@require_safe
@require_http_methods(['GET'])
@permission_required('mediaserver.change_gallery')
def get_gallery_media(request: HttpRequest, gallery_id: int):
    gallery = get_object_or_404(Gallery, pk=gallery_id)
    items = gallery.media_items.order_by('galleryorder')
    media = []
    for item in items:
        discord_creator = item.discord_creator.username if item.discord_creator else ""
        discord_creator_tag = [{'tagname': item.discord_creator.tag.tagname, 'namespace': 'creator'}
            ] if item.discord_creator and item.discord_creator.tag else []

        media.append({
            'uuid': item.uuid,
            'url': item.file.url,
            'type': item.type,
            'title': item.title,
            'description': item.description,
            'uploaderDescription': item.uploaderDescription,
            'loop': item.loop,
            'creator_tags': [{'namespace': 'creator', 'tagname': tag.tagname} for tag in item.creator_tags.all()],
            'discord_creator': discord_creator,
            'discord_creator_tag': discord_creator_tag,
            'tags': [{'namespace': tag.namespace, 'tagname': tag.tagname} for tag in item.tags.all()],
        })
    return JsonResponse(media, safe=False)

@require_safe
@require_http_methods(['GET'])
@permission_required('mediaserver.change_gallery')
def get_gallery_metadata(request: HttpRequest, gallery_id: int):
    gallery = get_object_or_404(Gallery, pk=gallery_id)
    return JsonResponse({
            'id': gallery.id,
            'title': gallery.title, 
            'category': gallery.category,
            'visible': gallery.visible,
            'created_date': gallery.created_date.date(),
        }, safe=False)

@require_safe
@require_http_methods(['GET'])
@permission_required('mediaserver.change_gallery')
def get_categories(request: HttpRequest):
    categories = Gallery.objects.all().distinct('category').values_list('category', flat=True)
    return JsonResponse(list(categories), safe=False)

@login_required
@require_http_methods(['POST'])
@permission_required('mediaserver.add_media')
def create_embedded_media(request: HttpRequest):
    tempDict = request.POST.copy()
    tempDict['uploader'] = request.user # type: ignore
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
                removed_tag.count_uses()

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
                removed_tag.count_uses()

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
def update_gallery_media(request: HttpRequest, gallery_id: int):
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
def update_gallery_title(request: HttpRequest, gallery_id: int):
    gallery = Gallery.objects.get(id=gallery_id)
    gallery.title = request.body.decode()
    gallery.save()
    return HttpResponse(f'{gallery.title}')

@login_required
@require_http_methods(["POST"])
@permission_required('mediaserver.change_gallery')
def update_gallery_visibility(request: HttpRequest, gallery_id: int):
    gallery = Gallery.objects.get(id=gallery_id)
    gallery.visible = not gallery.visible
    gallery.save()
    return HttpResponse(f'{gallery.visible}')

@login_required
@require_http_methods(["POST"])
@permission_required('mediaserver.change_gallery')
def update_gallery_date(request: HttpRequest, gallery_id: int):
    gallery = Gallery.objects.get(id=gallery_id)
    gallery.created_date = datetime.fromisoformat(f'{request.body.decode()}T00:00:00Z')
    gallery.save()
    return HttpResponse(f'{gallery.created_date}')

@login_required
@require_http_methods(["POST"])
@permission_required('mediaserver.change_gallery')
def update_gallery_category(request: HttpRequest, gallery_id: int):
    gallery = Gallery.objects.get(id=gallery_id)
    gallery.category = request.body.decode()
    gallery.save()
    return HttpResponse(f'Updated #{gallery_id} category')

@login_required
@require_http_methods(["POST"])
@permission_required('mediaserver.change_gallery')
def associate_media(request: HttpRequest, gallery_id: int):
    #expect body in form of 'uuid,order'
    uuid, order = request.body.decode().split(',')
    gallery = Gallery.objects.get(id=gallery_id)
    media = Media.objects.get(uuid=uuid)
    gallery.media_items.add(media, through_defaults={'order': order})
    return HttpResponse(status=200)

@login_required
@require_http_methods(["POST"])
@permission_required('mediaserver.change_gallery')
def add_single_media(request: HttpRequest, gallery_id: int):
    media = Media.objects.get(uuid=request.body.decode())
    gallery = Gallery.objects.get(id=gallery_id)
    gallery.media_items.add(media, through_defaults={'order': gallery.media_items.count()})
    return HttpResponse(status=200)

@login_required
@require_http_methods(["POST"])
@permission_required('mediaserver.add_gallery')
def create_gallery(request: HttpRequest):
    new_gallery = Gallery(title="New Gallery", category="other")
    new_gallery.save()
    return HttpResponseRedirect(reverse('edit_gallery', args=([new_gallery.id])))
    
@login_required
@require_http_methods(["POST"])
@permission_required('mediaserver.delete_gallery')
def delete_gallery(request: HttpRequest, gallery_id: int):
    gallery = Gallery.objects.get(id=gallery_id)
    for media_item in gallery.media_items.all():
        media_item.delete()
    gallery.delete()
    return HttpResponseRedirect('/')

@login_required
@require_http_methods(["POST"])
@permission_required('mediaserver.delete_gallery')
def delete_media(request: HttpRequest, media_uuid: UUID):
    media = Media.objects.get(uuid=media_uuid)
    media.delete()
    return HttpResponseRedirect(reverse('orphaned_media'))

@login_required
@require_http_methods(["POST"])
@permission_required('mediaserver.change_media')
def detach_media(request: HttpRequest, media_uuid: UUID):
    media = Media.objects.get(uuid=media_uuid)
    media.media_gallery.clear() # type: ignore
    return HttpResponseRedirect(reverse('orphaned_media'))

@login_required
@permission_required('mediaserver.change_gallery')
def orphaned_media(request: HttpRequest):
    orphaned_media = Media.objects.filter(media_gallery=None).order_by('uploaded_date')
    galleries = Gallery.objects.all().values('id', 'title').order_by('category', '-created_date')
    return render(request, "galleries/orphaned_media.html", {'orphaned_media': orphaned_media, 'galleries': galleries})

@login_required
@permission_required('mediaserver.change_media')
def set_discord_user(request: HttpRequest):
    media = Media.objects.get(uuid=request.POST['media_uuid'])
    discord_user = DiscordCreator.objects.get_or_create(username=request.POST['discord_user'])[0]
    media.discord_creator = discord_user
    media.save()
    if discord_user.tag:
        discord_user.tag.count_uses()
    return HttpResponse(status=200)

@login_required
@permission_required('mediaserver.change_media')
def remove_discord_user(request: HttpRequest):
    media = Media.objects.get(uuid=request.POST['uuid'])
    discord_user = media.discord_creator
    media.discord_creator = None
    media.save()
    if discord_user and discord_user.tag:
        discord_user.tag.count_uses()

    return HttpResponse(status=200)

@login_required
@permission_required('mediaserver.change_media')
def set_discord_user_tag(request: HttpRequest):
    discord_user = DiscordCreator.objects.get_or_create(username=request.POST['creator'])[0]
    if request.POST['tag'] and request.POST['tag'] != '':
        tag = Tag.objects.get_or_create(namespace='creator', tagname=request.POST['tag'])[0]
        prev_tag = discord_user.tag
        discord_user.tag = tag
        discord_user.save()

        if prev_tag:
            prev_tag.count_uses()
        tag.count_uses()

        return HttpResponse(status=200)
    return HttpResponse(status=200)

@receiver(post_delete, sender=Media)
def auto_delete_file_on_delete(sender: Media, instance: Media, **kwargs):
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
        q = Q(creator_tags__tagname__iexact=key) | Q(discord_creator__tag__tagname__iexact=key)
        queryset = Media.objects.filter(q).order_by('uploaded_date').distinct().reverse()
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['tag'] = Tag.objects.get(namespace='creator', tagname__iexact=self.kwargs.get('tag'))
        except ObjectDoesNotExist:
            raise Http404(f'No creator with name "{self.kwargs.get("tag")}"')
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
            try:
                context['tag'] = Tag.objects.get(tagname__iexact=self.kwargs.get('tag'))
            except ObjectDoesNotExist:
                raise Http404(f'No namespaceless tag with name "{self.kwargs.get("tag")}"')
        else:
            try:
                context['tag'] = Tag.objects.get(namespace__iexact=self.kwargs.get('namespace'), tagname__iexact=self.kwargs.get('tag'))
            except ObjectDoesNotExist:
                raise Http404(f'No "{self.kwargs.get("namespace")}" tag with name "{self.kwargs.get("tag")}"')
        return context