from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse

from pybb.models import AnonymousPost, Topic
from pybb import settings as pybb_settings

def handle_anonymous_post(request, topic_id):
    """
    Saves post content submitted by unauthorized users before
    redirect to the login page.
    """

    url = '%s?%s=%s' % (reverse('auth_login'), REDIRECT_FIELD_NAME, request.path)
    response = HttpResponseRedirect(url)

    if topic_id:
        topic = get_object_or_404(Topic, pk=topic_id)
        key = pybb_settings.ANONYMOUS_POST_COOKIE_NAME # I just don't like long lines :-)
        if not key in request.COOKIES:
            response.set_cookie(key, request.session.session_key)
            session_key = request.session.session_key
        else:
            session_key = request.COOKIES[key]

        apost = AnonymousPost(topic=topic, session_key=session_key,
                              body=request.POST.get('body', ''),
                              markup=request.POST.get('markup', ''))
        apost.save()
    return response


def load_anonymous_post(request, topic):
    """
    Try to load previously saved anonymous post for current user and topic.
    """

    try:
        key = request.COOKIES.get(pybb_settings.ANONYMOUS_POST_COOKIE_NAME, None)
        apost = AnonymousPost.objects.filter(topic=topic, session_key=key).order_by('-created')[0]
    except IndexError:
        apost = None
    return apost


def delete_anonymous_post(request, topic):
    """
    Delete any existing anonymous post for current user and topic.
    """

    key = request.COOKIES.get(pybb_settings.ANONYMOUS_POST_COOKIE_NAME, None)
    AnonymousPost.objects.filter(topic=topic, session_key=key).delete()
