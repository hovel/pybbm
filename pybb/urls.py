from django.conf.urls.defaults import *

from pybb.feeds import LastPosts, LastTopics


feeds = {
    'posts': LastPosts,
    'topics': LastTopics
}

urlpatterns = patterns('',
                       # Syndication feeds
                       url('^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed',
                           {'feed_dict': feeds}, name='feed'),
                       )

urlpatterns += patterns('pybb.views',
                        # Index, Category, Forum
                        url('^$', 'index', name='index'),
                        url('^category/(\d+)/$', 'show_category', name='category'),
                        url('^forum/(\d+)/$', 'show_forum', name='forum'),

                        # User
                        url('^users/([^/]+)/$', 'user', name='user'),
                        url('^block_user/([^/]+)/$', 'block_user', name='block_user'),

                        # Profile
                        url('^profile/edit/$', 'edit_profile', name='edit_profile'),

                        # Topic
                        url('^topic/(\d+)/$', 'show_topic', name='topic'),
                        url('^topic/(\d+)/stick/$', 'stick_topic', name='stick_topic'),
                        url('^topic/(\d+)/unstick/$', 'unstick_topic', name='unstick_topic'),
                        url('^topic/(\d+)/close/$', 'close_topic', name='close_topic'),
                        url('^topic/(\d+)/open/$', 'open_topic', name='open_topic'),

                        # Add topic/post
                        url('^forum/(?P<forum_id>\d+)/topic/add/$', 'add_post',
                            {'topic_id': None}, name='add_topic'),
                        url('^topic/(?P<topic_id>\d+)/post/add/$', 'add_post',
                            {'forum_id': None}, name='add_post'),

                        # Post
                        url('^post/(\d+)/$', 'show_post', name='post'),
                        url('^post/(\d+)/edit/$', 'edit_post', name='edit_post'),
                        url('^post/(\d+)/delete/$', 'delete_post', name='delete_post'),

                        # Attachment
                        #url('^attachment/(\w+)/$', 'show_attachment', name='pybb_attachment'),

                        # Subscription
                        url('^subscription/topic/(\d+)/delete/$',
                            'delete_subscription', name='delete_subscription'),
                        url('^subscription/topic/(\d+)/add/$',
                            'add_subscription', name='add_subscription'),

                        # API
                        url('^api/post_ajax_preview/$', 'post_ajax_preview', name='post_ajax_preview'),

                        # Commands
                        url('^mark_all_as_read/$', 'mark_all_as_read', name='mark_all_as_read')
                        )
