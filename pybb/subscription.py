from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.utils import translation
from django.contrib.sites.models import Site
from django.core.mail import send_mail


TOPIC_SUBSCRIPTION_TEXT_TEMPLATE = lambda: _(u"""New reply from %(username)s to topic that you have subscribed on.
---
%(message)s
---
See topic: %(post_url)s
Unsubscribe %(unsubscribe_url)s""")


def notify_topic_subscribers(post):
    from pybb.models import Post

    topic = post.topic
    if post != topic.head:
        for user in topic.subscribers.all():
            if user != post.user:
                old_lang = translation.get_language()
                lang = user.pybb_profile.language or 'en'
                translation.activate(lang)

                subject = u'RE: %s' % topic.name
                to_email = user.email
                hostname = Site.objects.get_current().domain
                delete_url = reverse('pybb_delete_subscription', args=[post.topic.id])

                content = TOPIC_SUBSCRIPTION_TEXT_TEMPLATE() % {
                    'username': post.user.username,
                    'message': post.body_text,
                    'post_url': 'http://%s%s' % (hostname, post.get_absolute_url()),
                    'unsubscribe_url': 'http://%s%s' % (hostname, delete_url),
                }

                send_mail(subject, content, settings.DEFAULT_FROM_EMAIL,
                          [to_email], fail_silently=True)
                translation.activate(old_lang)
