Updating PyBBM Version
======================

0.9 -> 0.10
-----------

* Templates are updated for 2nd version of twitter bootstrap
* Example app now splitted with two versions, in one case you have buildin twitter bootstrap, in second case you just use pinax-theme-bootstrap and django-forms-bootstrap that provides bootstrap for you and simplify templates development.


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