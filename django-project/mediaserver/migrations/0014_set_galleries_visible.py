from django.db import models, migrations

def set_visible(apps, schema_editor):
    Gallery = apps.get_model('mediaserver', 'Gallery')

    for gallery in Gallery.objects.all():
        gallery.visible = True
        gallery.save()

class Migration(migrations.Migration):
    
        dependencies = [
            ('mediaserver', '0013_gallery_visible'),
        ]
    
        operations = [
            migrations.RunPython(set_visible),
        ]