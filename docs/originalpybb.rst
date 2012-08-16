PyBB Modified (PyBBM) and original PyBB
=======================================

PyBB originally developed by lorien in 2008-2010 has ben dropped from development in mid 2010.

This is a list of differences between PyBB and PyBBM as of mid 2011.

* PyBBM uses get_profile() anywhere to populate additional user information.
* All settings of pybbm have default values, see default.py file for detailed list.
* pybbm templates fill *content*, *head*, *title* and *breadcrumb* blocks for template defined in settings as PYBB_TEMPLATE ("base.html" by default).
* Markup engines can be configured as an ordinary settings.
* PyBBM designed to fit django-staticfiles (django <= 1.2) or django.contrib.staticfiles (django >= 1.3).
* Default pybbm templates and css files include only layout, minimal design and no coloring, so it's easy to fit any existed site colorscheme.
* PyBBM code covered with tests more than 80%
* PyBBM provides completely rewritten unread tracking with big performance improvement on large database
* Views rewritten to use as many generics as possible
* Number of external dependencies significantly reduced
* `PyBBM well documented <http://readthedocs.org/projects/pybbm/>`_
* PyBBM included two example projects for fast start.