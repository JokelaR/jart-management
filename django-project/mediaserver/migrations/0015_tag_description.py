# Generated by Django 5.1 on 2025-01-04 15:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mediaserver', '0014_set_galleries_visible'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='description',
            field=models.TextField(blank=True),
        ),
    ]
