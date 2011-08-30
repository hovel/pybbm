PyBBM Django forum solution
===========================
PyBBM - modified version of pybb (developed by lorien and dropped in mid 2010).

`Documentation aviable on ReadTheDocs <http://readthedocs.org/projects/pybbm/>`_

PyBBM includes ready to use `example/test project with instructions <http://readthedocs.org/docs/pybbm/en/latest/example.html>`_

The main point in development of pybb is to build it so it could be
*easily* integrated to existing django based site. This mean:

* pybb does not provide features like user registration, password restoring.
  It does not provide authentication page. You should use your favorite
  application for such things. You can try well known django-registration
  http://code.google.com/p/django-registration/.

i18n support
============
PYBB support only english and russian translations now.
You should enable django.middleware.locale.LocaleMiddleware to activate
django locale autodetecting.
