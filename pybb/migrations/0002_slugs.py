# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from pybb.models import create_or_check_slug


def fill_slugs(apps, schema_editor):
    Category = apps.get_model("pybb", "Category")
    Forum = apps.get_model("pybb", "Forum")
    Topic = apps.get_model("pybb", "Topic")
    for category in Category.objects.all():
        category.slug = create_or_check_slug(instance=category, model=Category)
        category.save()

    for forum in Forum.objects.all():
        extra_filters = {'category': forum.category}
        forum.slug = create_or_check_slug(instance=forum, model=Forum, **extra_filters)
        forum.save()

    for topic in Topic.objects.all():
        extra_filters = {'forum': topic.forum}
        topic.slug = create_or_check_slug(instance=topic, model=Topic, **extra_filters)
        topic.save()


def clear_slugs(apps, schema_editor):
    Category = apps.get_model("pybb", "Category")
    Forum = apps.get_model("pybb", "Forum")
    Topic = apps.get_model("pybb", "Topic")

    Category.objects.all().update(slug='')
    Forum.objects.all().update(slug='')
    Topic.objects.all().update(slug='')


class Migration(migrations.Migration):

    dependencies = [
        ('pybb', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='slug',
            field=models.SlugField(max_length=255, verbose_name='Slug', blank=True),
        ),
        migrations.AddField(
            model_name='forum',
            name='slug',
            field=models.SlugField(max_length=255, verbose_name='Slug', blank=True),
        ),
        migrations.AddField(
            model_name='topic',
            name='slug',
            field=models.SlugField(max_length=255, verbose_name='Slug', blank=True),
        ),

        migrations.RunPython(fill_slugs, clear_slugs),

        migrations.AlterField(
            model_name='category',
            name='slug',
            field=models.SlugField(unique=True, max_length=255, verbose_name='Slug'),
        ),
        migrations.AlterField(
            model_name='forum',
            name='slug',
            field=models.SlugField(max_length=255, verbose_name='Slug'),
        ),
        migrations.AlterField(
            model_name='topic',
            name='slug',
            field=models.SlugField(max_length=255, verbose_name='Slug'),
        ),
        migrations.AlterUniqueTogether(
            name='forum',
            unique_together=set([('category', 'slug')]),
        ),
        migrations.AlterUniqueTogether(
            name='topic',
            unique_together=set([('forum', 'slug')]),
        ),
    ]
