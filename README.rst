PyBBM Django forum solution
=============
PyBBM - modified version of pybb (developed by lorien and dropped in mid 2010).

`Documentation aviable on ReadTheDocs <http://readthedocs.org/projects/pybbm/>`_

PyBBM includes ready to use `example/test project with instructions <http://readthedocs.org/docs/pybbm/en/latest/example.html>`_

The main point in development of pybb is to build it so it could be
*easily* integrated to existing django based site. This mean:

* pybb does not provide features like user registration, password restoring.
  It does not provide authentication page. You should use your favorite
  application for such things. You can try well known django-registration
  http://code.google.com/p/django-registration/.

* PyBB Modified features against original PyBB:
  * pybbm uses get_profile() anywhere to populate additional user information.
  * All settings of pybbm have default values, see default.py file for detailed list.
  * pybbm templates fill *content*, *head*, *title* and *breadcrumb* blocks for template defined
    in settings as PYBB_TEMPLATE ("base.html" by default).
  * Markup engines can be configured as an ordinary settings.
  * pybbm designed to fit django-staticfiles (django <= 1.2) or django.contrib.staticfiles (django >= 1.3).
  * Default pybbm templates and css files include only layout, minimal design and
   no coloring, so it's easy to fit any existed site colorscheme.
  * PyBBM code covered with tests more than 80%
  * PyBBM provides completely rewritten unread tracking with big performance improvement on large database
  * Views rewritten to use as many generics as possible
  * Number of external dependencies significantly reduced
  * `pybbm well documented <http://readthedocs.org/projects/pybbm/>`_
  * pybbm included example project for fast start.


i18n support
============
PYBB support only english and russian translations now.
You should enable django.middleware.locale.LocaleMiddleware to activate
django locale autodetecting.
