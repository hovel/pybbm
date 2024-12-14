

from django.urls import re_path

from pybb.defaults import PYBB_NICE_URL
from pybb.feeds import LastPosts, LastTopics
from pybb.views import IndexView, CategoryView, ForumView, TopicView, \
    AddPostView, EditPostView, MovePostView, UserView, PostView, ProfileEditView, \
    DeletePostView, StickTopicView, UnstickTopicView, CloseTopicView, \
    OpenTopicView, ModeratePost, TopicPollVoteView, LatestTopicsView, \
    UserTopics, UserPosts, topic_cancel_poll_vote, block_user, unblock_user, \
    delete_subscription, add_subscription, post_ajax_preview, \
    mark_all_as_read, ForumSubscriptionView, UserEditPrivilegesView

app_name = 'pybbm'

urlpatterns = [
    # Syndication feeds
    re_path('^feeds/posts/$', LastPosts(), name='feed_posts'),
    re_path('^feeds/topics/$', LastTopics(), name='feed_topics'),
]

urlpatterns += [
    # Index, Category, Forum
    re_path('^$', IndexView.as_view(), name='index'),
    re_path('^category/(?P<pk>\d+)/$', CategoryView.as_view(), name='category'),
    re_path('^forum/(?P<pk>\d+)/$', ForumView.as_view(), name='forum'),

    # User
    re_path('^users/(?P<username>[^/]+)/$', UserView.as_view(), name='user'),
    re_path('^block_user/([^/]+)/$', block_user, name='block_user'),
    re_path('^unblock_user/([^/]+)/$', unblock_user, name='unblock_user'),
    re_path(r'^users/(?P<username>[^/]+)/topics/$', UserTopics.as_view(),
        name='user_topics'),
    re_path(r'^users/(?P<username>[^/]+)/posts/$', UserPosts.as_view(),
        name='user_posts'),
    re_path(r'^users/(?P<username>[^/]+)/edit-privileges/$',
        UserEditPrivilegesView.as_view(), name='edit_privileges'),

    # Profile
    re_path('^profile/edit/$', ProfileEditView.as_view(), name='edit_profile'),

    # Topic
    re_path('^topic/(?P<pk>\d+)/$', TopicView.as_view(), name='topic'),
    re_path('^topic/(?P<pk>\d+)/stick/$', StickTopicView.as_view(),
        name='stick_topic'),
    re_path('^topic/(?P<pk>\d+)/unstick/$', UnstickTopicView.as_view(),
        name='unstick_topic'),
    re_path('^topic/(?P<pk>\d+)/close/$', CloseTopicView.as_view(),
        name='close_topic'),
    re_path('^topic/(?P<pk>\d+)/open/$', OpenTopicView.as_view(),
        name='open_topic'),
    re_path('^topic/(?P<pk>\d+)/poll_vote/$', TopicPollVoteView.as_view(),
        name='topic_poll_vote'),
    re_path('^topic/(?P<pk>\d+)/cancel_poll_vote/$', topic_cancel_poll_vote,
        name='topic_cancel_poll_vote'),
    re_path('^topic/latest/$', LatestTopicsView.as_view(), name='topic_latest'),

    # Add topic/post
    re_path('^forum/(?P<forum_id>\d+)/topic/add/$', AddPostView.as_view(),
        name='add_topic'),
    re_path('^topic/(?P<topic_id>\d+)/post/add/$', AddPostView.as_view(),
        name='add_post'),

    # Post
    re_path('^post/(?P<pk>\d+)/$', PostView.as_view(), name='post'),
    re_path('^post/(?P<pk>\d+)/edit/$', EditPostView.as_view(), name='edit_post'),
    re_path('^post/(?P<pk>\d+)/move/$', MovePostView.as_view(), name='move_post'),
    re_path('^post/(?P<pk>\d+)/delete/$', DeletePostView.as_view(),
        name='delete_post'),
    re_path('^post/(?P<pk>\d+)/moderate/$', ModeratePost.as_view(),
        name='moderate_post'),

    # Attachment
    # url('^attachment/(\w+)/$', 'show_attachment', name='pybb_attachment'),

    # Subscription
    re_path('^subscription/topic/(\d+)/delete/$',
        delete_subscription, name='delete_subscription'),
    re_path('^subscription/topic/(\d+)/add/$',
        add_subscription, name='add_subscription'),
    re_path('^subscription/forum/(?P<pk>\d+)/$',
        ForumSubscriptionView.as_view(), name='forum_subscription'),

    # API
    re_path('^api/post_ajax_preview/$', post_ajax_preview,
        name='post_ajax_preview'),

    # Commands
    re_path('^mark_all_as_read/$', mark_all_as_read, name='mark_all_as_read')
]

if PYBB_NICE_URL:
    urlpatterns += [
        re_path(r'^c/(?P<slug>[\w-]+)/$', CategoryView.as_view(), name='category'),
        re_path(r'^c/(?P<category_slug>[\w-]+)/(?P<slug>[\w-]+)/$',
            ForumView.as_view(),
            name='forum'),
        re_path(
            r'^c/(?P<category_slug>[\w-]+)/(?P<forum_slug>[\w-]+)/(?P<slug>[\w-]+)/$',
            TopicView.as_view(), name='topic'),
    ]
