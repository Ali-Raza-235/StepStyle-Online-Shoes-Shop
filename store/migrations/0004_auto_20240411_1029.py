# Generated by Django 3.1 on 2024-04-11 05:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_variations'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Variations',
            new_name='Variation',
        ),
    ]