# Generated by Django 3.1.3 on 2022-04-22 00:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='feedback',
            old_name='comment',
            new_name='text',
        ),
    ]
