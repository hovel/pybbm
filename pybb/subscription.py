from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.core.urlresolvers import reverse

def notify_subscribers(post):
    from pybb.models import Post

    topic = post.topic
    if post != topic.head:
        for user in topic.subscribers.all():
            if user != post.user:
                subject = u'RE: %s' % topic.name
                from_email = settings.DEFAULT_FROM_EMAIL
                to_email = user.email
                text_content = text_version(post)
                #html_content = html_version(post)
                msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
                #msg.attach_alternative(html_content, "text/html")
                msg.send(fail_silently=True)


TEXT_TEMPLATE = u"""New reply from %s to topic that you have subscribed on.
---
%s
---
See topic: %s
Unsubscribe %s"""

def text_version(post):
    data = TEXT_TEMPLATE % (
        post.user.username,
        post.body_text,
        absolute_url(post.get_absolute_url()),
        absolute_url(reverse('pybb_delete_subscription', args=[post.topic.id])),
    )
    return data

def absolute_url(uri):
    return 'http://%s%s' % (settings.PYBB_HOST, uri)
