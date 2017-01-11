# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pybb', '0006_forum_subscriptions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='updated',
            field=models.DateTimeField(db_index=True, null=True, verbose_name='Updated', blank=True),
        ),
        migrations.AlterField(
            model_name='topic',
            name='created',
            field=models.DateTimeField(null=True, verbose_name='Created', db_index=True),
        ),
        migrations.AlterField(
            model_name='topic',
            name='updated',
            field=models.DateTimeField(null=True, verbose_name='Updated', db_index=True),
        ),
    ]
