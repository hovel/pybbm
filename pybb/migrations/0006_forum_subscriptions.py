# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
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
                ('type', models.PositiveSmallIntegerField(
                    help_text='The auto-subscription works like you manually subscribed to watch each topic :\n'
                              'you will be notified when a topic will receive an answer. \n'
                              'If you choose to be notified only when a new topic is added. It means'
                              'you will be notified only once when the topic is created : '
                              'you won\'t be notified for the answers.',
                    verbose_name='Subscription type', choices=[(1, 'be notified only when a new topic is added'), (2, 'be auto-subscribed to topics')])),
                ('forum', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions+', verbose_name='Forum', to='pybb.Forum')),
                ('user', models.ForeignKey(related_name='forum_subscriptions+', on_delete=models.CASCADE, verbose_name='Subscriber', to=settings.AUTH_USER_MODEL)),
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
