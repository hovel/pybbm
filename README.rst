PyBBM - Django forum solution
=============================

PyBBM is a full-featured django forum solution with these features:

* Avatars
* Custom profiles
* Post editing
* Pre-moderation
* Custom sanitization
* Anonymous posting
* Subscriptions
* Polls
* ...

All features is based on:

* 95% tests covered code
* Twitter bootstrap 2 default theme
* Ready to use example project

The main point in development of pybb is to build it so it could be
*easily* integrated to existing django based site. This mean that pybb does not provide features like user registration, password restoring.  It does not provide authentication page. (But example project provides ;))

`Documentation available on ReadTheDocs <http://pybbm.readthedocs.org/en/latest/>`_

PyBBM includes ready to use `example/test project with instructions <http://readthedocs.org/docs/pybbm/en/latest/example.html>`_

i18n support
============
PYBB support only english and russian translations now.
You should enable django.middleware.locale.LocaleMiddleware to activate
django locale autodetecting.
