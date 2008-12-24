from django.conf.urls.defaults import *

from pybb import views
from pybb.feeds import LastPosts, LastTopics

feeds = {
    'posts': LastPosts,
    'topics': LastTopics,
}

urlpatterns = patterns('',
    # Misc
    url('^$', views.index, name='index'),
    url('^category/(?P<category_id>\d+)/$', views.show_category, name='category'),
    url('^forum/(?P<forum_id>\d+)/$', views.show_forum, name='forum'),
    url('^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed',
        {'feed_dict': feeds}, name='pybb_feed'),

    # User
    url('^user/(?P<username>.*)/$', views.user, name='pybb_profile'),
    url('^profile/edit/$', views.edit_profile, name='edit_profile'),
    url('^users/$', views.users, name='pybb_users'),

    # Topic
    url('^topic/(?P<topic_id>\d+)/$', views.show_topic, name='topic'),
    url('^forum/(?P<forum_id>\d+)/topic/add/$', views.add_post,
        {'topic_id': None}, name='add_topic'),
    url('^topic/(?P<topic_id>\d+)/stick/$', views.stick_topic, name='stick_topic'),
    url('^topic/(?P<topic_id>\d+)/unstick/$', views.unstick_topic, name='unstick_topic'),
    url('^topic/(?P<topic_id>\d+)/close/$', views.close_topic, name='close_topic'),
    url('^topic/(?P<topic_id>\d+)/open/$', views.open_topic, name='open_topic'),

    # Post
    url('^topic/(?P<topic_id>\d+)/post/add/$', views.add_post,
        {'forum_id': None}, name='add_post'),
    url('^post/(?P<post_id>\d+)/$', views.show_post, name='post'),
    url('^post/(?P<post_id>\d+)/edit/$', views.edit_post, name='edit_post'),
    url('^post/(?P<post_id>\d+)/delete/$', views.delete_post, name='delete_post'),

    # Subscription
    url('^subscription/topic/(?P<topic_id>\d+)/delete/$', views.delete_subscription, name='pybb_delete_subscription'),
    url('^subscription/topic/(?P<topic_id>\d+)/add/$', views.add_subscription, name='pybb_add_subscription'),

    # Private messages
    url('^pm/new/$', views.create_pm, name='pybb_create_pm'),
    url('^pm/outbox/$', views.pm_outbox, name='pybb_pm_outbox'),
    url('^pm/inbox/$', views.pm_inbox, name='pybb_pm_inbox'),
)
