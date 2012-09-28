Updating PyBBM Version
======================

0.10 - 0.11
-----------

* Ability to override standard message when user doesn't login and not alowed anonymous posts by
``PYBB_ENABLE_ANONYMOUS_POST`` setting. It may be useful when project doesn't have ``registration_register``
and/or ``auth_login`` url names in ``urls.py``

* Content in each ``topic.html`` and ``forum.html`` is wrapped in ``<div>`` tag with ``topic`` and ``forum`` classes
accordingly

0.9 -> 0.10
-----------

* Templates are updated for 2nd version of twitter bootstrap
* Bootstrap less files removed from pybb.
* Refactored example projects. `test` folder now contains two examples:
    * `example_bootstrap` shows how to include bootstrap files in your project
    * `example_thirdparty` shows how to use another project like `pinax-theme-bootstrap <https://github.com/pinax/pinax-theme-bootstrap>`_ to style forum
* New poll feature added. When user creates new topic he can add poll question and some answers. Answers count
  can vary from 2 to PYBB_POLL_MAX_ANSWERS setting (10 by default)
* Dropped support for self containing CSS in pybb.css file and PYBB_ENABLE_SELF_CSS setting.

0.8 -> 0.9
----------

The PYBB_BUTTONS setting is removed and overridable `pybb/_button_*.html`
templates for `save`, `new topic` and `submit` buttons are provided in case
css styling methods are not enough.

0.6 -> 0.7
----------

If you use custom BODY_CLEANER in your settings, rename this setting to PYBB_BODY_VALIDATOR

0.5 -> 0.6
----------

Version 0.6 has significant changes in template subsystem, with main goal to make them more configurable and simple.

* CSS now not included with project.
    * For a limited time legacy `pybb.css` can be enabled by activating `PYBB_ENABLE_SELF_CSS` settings (just set it for True).
* Twitter bootstrap now included in project tree
* Default templates now provide fine theme with twitter bootstrap, corresponded .less file 'pybb_bootstrap.less'
  and builded `pybb_bootstrap.css` can be located in static. You can find example of usage in test directory.
* Pagination and breadcrumb templates changed:
    * pagination template moved from `templates/pybb/pagination/` to `templates/pybb`
    * pagination template changed from plain links to ul/li list
    * breadcrumb now live in separated template and changed from plain links to ul/li list
    * `add_post_form.html` template renamed to `post_form.html`
* PYBB_FORUM_PAGE_SIZE default value changed from 10 to 20