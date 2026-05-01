from django.db import models, migrations

def copy_dates(apps, schema_editor):
    Gallery = apps.get_model('mediaserver', 'Gallery')
    Media = apps.get_model('mediaserver', 'Media')

    for media in Media.objects.all():
        if media.media_gallery.count() > 0:
            print(media, 'updated')
            media.uploaded_date = media.media_gallery.all().first().created_date
            media.save()
        else:
            print(media, 'has no gallery!')

class Migration(migrations.Migration):
    
        dependencies = [
            ('mediaserver', '0009_alter_gallery_media_items'),
        ]
    
        operations = [
            migrations.RunPython(copy_dates),
        ]