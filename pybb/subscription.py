from django.conf import settings
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils import translation
from django.contrib.sites.models import Site
from django.core.mail import send_mail


def notify_topic_subscribers(post):
    topic = post.topic
    if post != topic.head:
        for user in topic.subscribers.all():
            if user != post.user:
                old_lang = translation.get_language()
                lang = user.get_profile().language or dict(settings.LANGUAGES)[settings.LANGUAGE_CODE.split('-')[0]]
                translation.activate(lang)
                delete_url = reverse('pybb:delete_subscription', args=[post.topic.id])
                current_site = Site.objects.get_current()
                subject = render_to_string('pybb/mail_templates/subscription_email_subject.html',
                                           { 'site': current_site,
                                             'post': post
                                           })
                # Email subject *must not* contain newlines
                subject = ''.join(subject.splitlines())
                message = render_to_string('pybb/mail_templates/subscription_email_body.html',
                                           { 'site': current_site,
                                             'post': post,
                                             'delete_url': delete_url,
                                             })
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
                translation.activate(old_lang)
