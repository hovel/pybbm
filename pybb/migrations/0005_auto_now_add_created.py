# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


def forwards_func(apps, schema_editor):
    Topic = apps.get_model("pybb", "Topic")
    Post = apps.get_model("pybb", "Post")
    db_alias = schema_editor.connection.alias
    Topic.objects.using(db_alias).filter(created=None).update(
        created=datetime.datetime.min
    )
    Post.objects.using(db_alias).filter(created=None).update(
        created=datetime.datetime.min
    )


class Migration(migrations.Migration):

    dependencies = [
        ('pybb', '0004_slugs_required'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
            migrations.RunPython.noop
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
