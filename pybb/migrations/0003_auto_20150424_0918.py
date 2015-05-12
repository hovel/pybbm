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


class Migration(migrations.Migration):

    dependencies = [
        ('pybb', '0002_auto_20150424_0918'),
    ]

    operations = [
        migrations.RunPython(fill_slugs),
    ]
