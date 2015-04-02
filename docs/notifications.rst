Notifications
=============

Configure notifications
-----------------------

See those settings:
* :ref:`PYBB_DISABLE_SUBSCRIPTIONS`
* :ref:`PYBB_DEFAULT_AUTOSUBSCRIBE`
* :ref:`PYBB_DISABLE_NOTIFICATIONS`
* :ref:`PYBB_USE_DJANGO_MAILER`

When notifications are sent
---------------------------

Each time a post is saved (created or updated), subcribers will receive an email.
If you configure PYBB to use django-mailer (see :ref:`PYBB_USE_DJANGO_MAILER`), emails
will be sent when your cron job will run. Else, emails will be sent when post is saved.

Overwrite emails templates
--------------------------

You can overwrite three templates:

* `pybb/mail_templates/subscription_email_subject.html`: will be used to render the subject of the email
* `pybb/mail_templates/subscription_email_body.html`: will be used to render the text version's body of the email
* `pybb/mail_templates/subscription_email_body-html.html`: will be used to render the html version's body of the email


My test user is not receiving emails ?!
---------------------------------------

Emails matching this rules are not sent: <username>@exemple.com
