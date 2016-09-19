# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('pybb', '0005_auto_20151108_1528'),
    ]

    operations = [
        migrations.CreateModel(
            name='ForumSubscription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.PositiveSmallIntegerField(help_text="The auto-subscription works like you manually subscribe to watch each topic :\nyou will receive a notification when a topic will receive an answer. \nIf you choose to be notified only when a new topic is added, you will only be notified once when the topic is created : if its receive answers later, you won't be notified", verbose_name='Subscription type', choices=[(1, 'be notified only when a new topic is added'), (2, 'be auto-subscribed to topics')])),
                ('forum', models.ForeignKey(related_name='subscriptions+', verbose_name='Subscriptions', to='pybb.Forum')),
                ('user', models.ForeignKey(related_name='forum_subscriptions+', verbose_name='Subscriber', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Subscription to forum',
                'verbose_name_plural': 'Subscriptions to forums',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='forumsubscription',
            unique_together=set([('user', 'forum')]),
        ),
    ]
