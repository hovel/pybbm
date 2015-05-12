# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pybb', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='slug',
            field=models.SlugField(max_length=100, verbose_name='Piece of URL', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='forum',
            name='slug',
            field=models.SlugField(max_length=100, verbose_name='Piece of URL', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='topic',
            name='slug',
            field=models.SlugField(max_length=100, verbose_name='Piece of URL', blank=True),
            preserve_default=True,
        ),
    ]
