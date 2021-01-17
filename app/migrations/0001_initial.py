# Generated by Django 3.0.8 on 2021-01-15 21:38

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(editable=False, upload_to='images/')),
                ('is_local', models.BooleanField(default=True)),
                ('hue', models.PositiveSmallIntegerField(default=0)),
                ('effective_from', models.DateTimeField(auto_now_add=True)),
                ('effective_to', models.DateTimeField(default=None)),
            ],
            options={
                'db_table': 'images',
            },
        ),
        migrations.AddIndex(
            model_name='image',
            index=models.Index(fields=['hue'], name='images_hue_8e6710_idx'),
        ),
        migrations.AddIndex(
            model_name='image',
            index=models.Index(fields=['hue', 'effective_to'], name='images_hue_54da1f_idx'),
        ),
    ]
