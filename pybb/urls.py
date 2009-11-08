from django.conf.urls.defaults import *

from pybb import views
from pybb.feeds import LastPosts, LastTopics

feeds = {
    'posts': LastPosts,
    'topics': LastTopics,
}

urlpatterns = patterns('',
    # Misc
    url('^$', views.index, name='pybb_index'),
    url('^category/(?P<category_id>\d+)/$', views.show_category, name='pybb_category'),
    url('^forum/(?P<forum_id>\d+)/$', views.show_forum, name='pybb_forum'),
    url('^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed',
        {'feed_dict': feeds}, name='pybb_feed'),

    # User
    #url('^user/(?P<username>.*)/posts/$', views.user_posts, name='pybb_profile_posts'),
    url('^user/(?P<username>.*)/topics/$', views.user_topics, name='pybb_profile_topics'),
    url('^user/(?P<username>.*)/$', views.user, name='pybb_profile'),
    url('^profile/edit/$', views.edit_profile, name='pybb_edit_profile'),
    url('^users/$', views.users, name='pybb_users'),

    # Topic
    url('^topic/(?P<topic_id>\d+)/$', views.show_topic, name='pybb_topic'),
    url('^topic/(?P<topic_id>\d+)/stick/$', views.stick_topic, name='pybb_stick_topic'),
    url('^topic/(?P<topic_id>\d+)/unstick/$', views.unstick_topic, name='pybb_unstick_topic'),
    url('^topic/(?P<topic_id>\d+)/close/$', views.close_topic, name='pybb_close_topic'),
    url('^topic/(?P<topic_id>\d+)/open/$', views.open_topic, name='pybb_open_topic'),
    url('^merge_topics/$', views.merge_topics, name='pybb_merge_topics'),

    # Add topic/post
    url('^forum/(?P<forum_id>\d+)/topic/add/$', views.add_post,
        {'topic_id': None}, name='pybb_add_topic'),
    url('^topic/(?P<topic_id>\d+)/post/add/$', views.add_post,
        {'forum_id': None}, name='pybb_add_post'),

    # Post
    url('^post/(?P<post_id>\d+)/$', views.show_post, name='pybb_post'),
    url('^post/(?P<post_id>\d+)/edit/$', views.edit_post, name='pybb_edit_post'),
    url('^post/(?P<post_id>\d+)/delete/$', views.delete_post, name='pybb_delete_post'),

    # Attachment
    url('^attachment/(?P<hash>\w+)/$', views.show_attachment, name='pybb_attachment'),

    # Subscription
    url('^subscription/topic/(?P<topic_id>\d+)/delete/$',
        views.delete_subscription, name='pybb_delete_subscription'),
    url('^subscription/topic/(?P<topic_id>\d+)/add/$',
        views.add_subscription, name='pybb_add_subscription'),

    # API
    url('^api/post_ajax_preview/$', views.post_ajax_preview, name='pybb_post_ajax_preview'),
)
