# Generated by Django 3.0.8 on 2021-01-15 23:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='image',
            name='images_hue_8e6710_idx',
        ),
        migrations.RemoveIndex(
            model_name='image',
            name='images_hue_54da1f_idx',
        ),
        migrations.RenameField(
            model_name='image',
            old_name='hue',
            new_name='hue1',
        ),
        migrations.AddField(
            model_name='image',
            name='hue2',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='image',
            name='hue3',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='image',
            name='hue4',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddIndex(
            model_name='image',
            index=models.Index(fields=['hue1', 'hue2', 'hue3', 'hue4'], name='images_hue1_9fa074_idx'),
        ),
        migrations.AddIndex(
            model_name='image',
            index=models.Index(fields=['hue1', 'hue2', 'hue3', 'hue4', 'effective_to'], name='images_hue1_034a12_idx'),
        ),
    ]
