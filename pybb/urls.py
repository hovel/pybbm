"""
Rule for naming urlpatterns, views, urls:

    url(r'/object/(\d+)/action/', views.action_object, name='pybb_action_object)

If we want for example make urlpattern for ban the user then:

    url(r'/user/(\w+)/ban/$', views.ban_user, name='pybb_ban_user')
"""
from django.conf.urls.defaults import *

from pybb import views
from pybb.feeds import LastPosts, LastTopics


feeds = {
    'posts': LastPosts,
    'topics': LastTopics,
}

urlpatterns = patterns('',
    # Syndication feeds
    url('^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed',
        {'feed_dict': feeds}, name='pybb_feed'),
)

urlpatterns += patterns('pybb.views',
    # Index, Category, Forum
    url('^$', 'index', name='pybb_index'),
    url('^category/(\d+)/$', 'show_category', name='pybb_category'),
    url('^forum/(\d+)/$', 'show_forum', name='pybb_forum'),

    # User
    url('^users/$', 'users', name='pybb_users'),
    url('^users/([^/]+)/$', 'user', name='pybb_user'),
    url('^users/([^/]+)/topics/$', 'user_topics', name='pybb_user_topics'),

    # Profile
    url('^profile/edit/$', 'edit_profile', name='pybb_edit_profile'),

    # Topic
    url('^topic/(\d+)/$', 'show_topic', name='pybb_topic'),
    url('^topic/(\d+)/stick/$', 'stick_topic', name='pybb_stick_topic'),
    url('^topic/(\d+)/unstick/$', 'unstick_topic', name='pybb_unstick_topic'),
    url('^topic/(\d+)/close/$', 'close_topic', name='pybb_close_topic'),
    url('^topic/(\d+)/open/$', 'open_topic', name='pybb_open_topic'),
    url('^merge_topics/$', 'merge_topics', name='pybb_merge_topics'),

    # Add topic/post
    url('^forum/(?P<forum_id>\d+)/topic/add/$', 'add_post',
        {'topic_id': None}, name='pybb_add_topic'),
    url('^topic/(?P<topic_id>\d+)/post/add/$', 'add_post',
        {'forum_id': None}, name='pybb_add_post'),

    # Post
    url('^post/(\d+)/$', 'show_post', name='pybb_post'),
    url('^post/(\d+)/edit/$', 'edit_post', name='pybb_edit_post'),
    url('^post/(\d+)/delete/$', 'delete_post', name='pybb_delete_post'),

    # Attachment
    url('^attachment/(\w+)/$', 'show_attachment', name='pybb_attachment'),

    # Subscription
    url('^subscription/topic/(\d+)/delete/$',
        'delete_subscription', name='pybb_delete_subscription'),
    url('^subscription/topic/(\d+)/add/$',
        'add_subscription', name='pybb_add_subscription'),

    # API
    url('^api/post_ajax_preview/$', 'post_ajax_preview', name='pybb_post_ajax_preview'),
)
