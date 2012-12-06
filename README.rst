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

PyBBM includes ready to use `example/test project with instructions <http://readthedocs.org/docs/pybbm/en/latest/example.html>`_

i18n support
============
PYBB support English, Russian, Slovak, Ukrainian, Brazilian Portuguese, Polish, Hebrew, French translations now. 
Feel free to contribute translation for another language or to correct existing.
You should enable django.middleware.locale.LocaleMiddleware to activate
django locale autodetecting.

More links
==========
* Support Forum and DEMO: http://pybbm.org/
* PyPi: http://pypi.python.org/pypi/pybbm/
* Sourcecode: https://github.com/hovel/pybbm/
* Documentation: http://pybbm.readthedocs.org/en/latest/
* Page on djangopackages.com: http://www.djangopackages.com/packages/p/pybbm/