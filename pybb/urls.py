from django.conf.urls.defaults import *

from pybb.feeds import LastPosts, LastTopics
from views import IndexView, CategoryView, ForumView, TopicView, AddPostView, EditPostView,\
    UserView, PostView, ProfileEditView, DeletePostView, StickTopicView, UnstickTopicView,\
    CloseTopicView, OpenTopicView, ModeratePost


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
                        url('^$', IndexView.as_view(), name='index'),
                        url('^category/(?P<pk>\d+)/$', CategoryView.as_view(), name='category'),
                        url('^forum/(?P<pk>\d+)/$', ForumView.as_view(), name='forum'),

                        # User
                        url('^users/(?P<username>[^/]+)/$', UserView.as_view(), name='user'),
                        url('^block_user/([^/]+)/$', 'block_user', name='block_user'),

                        # Profile
                        url('^profile/edit/$', ProfileEditView.as_view(), name='edit_profile'),

                        # Topic
                        url('^topic/(?P<pk>\d+)/$', TopicView.as_view(), name='topic'),
                        url('^topic/(?P<pk>\d+)/stick/$', StickTopicView.as_view(), name='stick_topic'),
                        url('^topic/(?P<pk>\d+)/unstick/$', UnstickTopicView.as_view(), name='unstick_topic'),
                        url('^topic/(?P<pk>\d+)/close/$', CloseTopicView.as_view(), name='close_topic'),
                        url('^topic/(?P<pk>\d+)/open/$', OpenTopicView.as_view(), name='open_topic'),

                        # Add topic/post
                        url('^forum/(?P<forum_id>\d+)/topic/add/$', AddPostView.as_view(), name='add_topic'),
                        url('^topic/(?P<topic_id>\d+)/post/add/$', AddPostView.as_view(), name='add_post'),

                        # Post
                        url('^post/(?P<pk>\d+)/$', PostView.as_view(), name='post'),
                        url('^post/(?P<pk>\d+)/edit/$', EditPostView.as_view(), name='edit_post'),
                        url('^post/(?P<pk>\d+)/delete/$', DeletePostView.as_view(), name='delete_post'),
                        url('^post/(?P<pk>\d+)/moderate/$', ModeratePost.as_view(), name='moderate_post'),

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
