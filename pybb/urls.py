

from django.conf.urls import url

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
    url('^feeds/posts/$', LastPosts(), name='feed_posts'),
    url('^feeds/topics/$', LastTopics(), name='feed_topics'),
]

urlpatterns += [
    # Index, Category, Forum
    url('^$', IndexView.as_view(), name='index'),
    url('^category/(?P<pk>\d+)/$', CategoryView.as_view(), name='category'),
    url('^forum/(?P<pk>\d+)/$', ForumView.as_view(), name='forum'),

    # User
    url('^users/(?P<username>[^/]+)/$', UserView.as_view(), name='user'),
    url('^block_user/([^/]+)/$', block_user, name='block_user'),
    url('^unblock_user/([^/]+)/$', unblock_user, name='unblock_user'),
    url(r'^users/(?P<username>[^/]+)/topics/$', UserTopics.as_view(),
        name='user_topics'),
    url(r'^users/(?P<username>[^/]+)/posts/$', UserPosts.as_view(),
        name='user_posts'),
    url(r'^users/(?P<username>[^/]+)/edit-privileges/$',
        UserEditPrivilegesView.as_view(), name='edit_privileges'),

    # Profile
    url('^profile/edit/$', ProfileEditView.as_view(), name='edit_profile'),

    # Topic
    url('^topic/(?P<pk>\d+)/$', TopicView.as_view(), name='topic'),
    url('^topic/(?P<pk>\d+)/stick/$', StickTopicView.as_view(),
        name='stick_topic'),
    url('^topic/(?P<pk>\d+)/unstick/$', UnstickTopicView.as_view(),
        name='unstick_topic'),
    url('^topic/(?P<pk>\d+)/close/$', CloseTopicView.as_view(),
        name='close_topic'),
    url('^topic/(?P<pk>\d+)/open/$', OpenTopicView.as_view(),
        name='open_topic'),
    url('^topic/(?P<pk>\d+)/poll_vote/$', TopicPollVoteView.as_view(),
        name='topic_poll_vote'),
    url('^topic/(?P<pk>\d+)/cancel_poll_vote/$', topic_cancel_poll_vote,
        name='topic_cancel_poll_vote'),
    url('^topic/latest/$', LatestTopicsView.as_view(), name='topic_latest'),

    # Add topic/post
    url('^forum/(?P<forum_id>\d+)/topic/add/$', AddPostView.as_view(),
        name='add_topic'),
    url('^topic/(?P<topic_id>\d+)/post/add/$', AddPostView.as_view(),
        name='add_post'),

    # Post
    url('^post/(?P<pk>\d+)/$', PostView.as_view(), name='post'),
    url('^post/(?P<pk>\d+)/edit/$', EditPostView.as_view(), name='edit_post'),
    url('^post/(?P<pk>\d+)/move/$', MovePostView.as_view(), name='move_post'),
    url('^post/(?P<pk>\d+)/delete/$', DeletePostView.as_view(),
        name='delete_post'),
    url('^post/(?P<pk>\d+)/moderate/$', ModeratePost.as_view(),
        name='moderate_post'),

    # Attachment
    # url('^attachment/(\w+)/$', 'show_attachment', name='pybb_attachment'),

    # Subscription
    url('^subscription/topic/(\d+)/delete/$',
        delete_subscription, name='delete_subscription'),
    url('^subscription/topic/(\d+)/add/$',
        add_subscription, name='add_subscription'),
    url('^subscription/forum/(?P<pk>\d+)/$',
        ForumSubscriptionView.as_view(), name='forum_subscription'),

    # API
    url('^api/post_ajax_preview/$', post_ajax_preview,
        name='post_ajax_preview'),

    # Commands
    url('^mark_all_as_read/$', mark_all_as_read, name='mark_all_as_read')
]

if PYBB_NICE_URL:
    urlpatterns += [
        url(r'^c/(?P<slug>[\w-]+)/$', CategoryView.as_view(), name='category'),
        url(r'^c/(?P<category_slug>[\w-]+)/(?P<slug>[\w-]+)/$',
            ForumView.as_view(),
            name='forum'),
        url(
            r'^c/(?P<category_slug>[\w-]+)/(?P<forum_slug>[\w-]+)/(?P<slug>[\w-]+)/$',
            TopicView.as_view(), name='topic'),
    ]
