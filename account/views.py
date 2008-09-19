# -*- coding: utf-8

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.utils.translation import ugettext as _, string_concat
from django.http import HttpResponseRedirect

from account.forms import RegistrationForm, RestorePasswordForm,\
                          NewPasswordForm, LoginForm
from account.util import email_template, build_redirect_url, render_to
from account.models import OneTimeCode


def message(msg):
    """
    Shortcut that prepare data for message view.
    """

    return {'TEMPLATE': 'account/message.html', 'message': msg}


@render_to('account/registration.html')
def registration(request):
    if request.user.is_authenticated():
        return message(_('You have to logout before registration'))
    if not getattr(settings, 'ACCOUNT_REGISTRATION', True):
        return message(_('Sorry. Registration is disabled.'))

    if 'POST' == request.method:
        form = RegistrationForm(request.POST)
    else:
        form = RegistrationForm()

    if form.is_valid():
        user = form.save()
        if getattr(settings, 'ACCOUNT_ACTIVATION', True):
            user.is_active = False
            user.save()
            url = 'http://%s%s' % (settings.DOMAIN, reverse('registration_complete'))
            url = OneTimeCode.objects.wrap_url(url, user, 'activation')
            params = {'domain': settings.DOMAIN, 'login': user.username, 'url': url}
            if email_template(user.email, 'account/mail/registration.txt', **params):
                return HttpResponseRedirect(reverse('account_created'))
            else:
                user.delete()
                return message(_('The error was occuried while sending email with activation code. Account was not created. Please, try later.'))
        else:
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            auth.login(request, user)    
            email_template(user.email, 'account/mail/welcome.txt',
                           **{'domain': settings.DOMAIN, 'login': user.username})
            return HttpResponseRedirect(reverse('registration_complete'))
    return {'form': form}


@render_to('account/message.html')
def logout(request):
    auth.logout(request)
    return message(_('You have successfuly logouted'))


@render_to('account/restore_password.html')
def restore_password(request):
    if 'POST' == request.method:
        form = RestorePasswordForm(request.POST)
    else:
        form = RestorePasswordForm()

    if form.is_valid():
        password = User.objects.make_random_password()
        user = User.objects.get(email=form.cleaned_data['email'])
        url = 'http://%s%s' % (settings.DOMAIN, reverse('auth_password_change'))
        url = OneTimeCode.objects.wrap_url(url, user, action='new_password',
                                           data=password)
        args = {'domain': settings.DOMAIN, 'url': url, 'password': password}
        if email_template(user.email, 'account/mail/restore_password.txt', **args):
            return message(_('Check the mail please'))
        else:
            return message(_('Unfortunately we could not send you email in current time. Please, try later'))
    return {'form': form}


@render_to('account/login.html')
def login(request):
    if request.user.is_authenticated():
        return message(_('You are already authenticated'))

    if 'POST' == request.method:
        form = LoginForm(request.POST, request=request)
    else:
        form = LoginForm(request=request)

    request.session['login_redirect_url'] = request.GET.get('next')
    if form.is_valid():
        redirect_url = build_redirect_url(request, settings.LOGIN_REDIRECT_URL)
        return HttpResponseRedirect(redirect_url)
    return {'form': form}


@login_required
@render_to('account/new_password.html')
def new_password(request):
    if 'POST' == request.method:
        form = NewPasswordForm(request.POST, user=request.user)
    else:
        form = NewPasswordForm(user=request.user)

    if form.is_valid():
        form.save()
        return message(_('Password was changed'))
    return {'form': form}
