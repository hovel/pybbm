# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations
from django.utils.timezone import make_aware
import datetime


def forwards_func(apps, schema_editor):
    Topic = apps.get_model("pybb", "Topic")
    Post = apps.get_model("pybb", "Post")
    db_alias = schema_editor.connection.alias
    min_datetime = datetime.datetime.min
    if settings.USE_TZ:
        min_datetime = make_aware(min_datetime)
    Topic.objects.using(db_alias).filter(created=None).update(
        created=min_datetime
    )
    Post.objects.using(db_alias).filter(created=None).update(
        created=min_datetime
    )

def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('pybb', '0004_slugs_required'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
            noop
        ),
        migrations.AlterField(
            model_name='post',
            name='created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created', db_index=True),
        ),
        migrations.AlterField(
            model_name='topic',
            name='created',
            field=models.DateTimeField(verbose_name='Created', auto_now_add=True),
            preserve_default=False,
        ),
    ]
