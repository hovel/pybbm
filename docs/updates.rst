Updating PyBBM Version
======================

0.13.1 -> dev
-------------

* Restored views for rendering user's posts and topics and link to that views from profile info page
* Broken hard dependency from EditProfileView and EditProfileForm classes in forum
* Ability for users to cancel their poll vote

0.13 -> 0.13.1
--------------

* Hotfix for rendering avatars

0.12.5 -> 0.13
--------------

* You can add first-unread get parameter to the topic url to provide link to first unread post from topic
* Removed django-mailer, pytils, sorl-thumbnail, south, django-pure-pagination from hard dependencies
* Support Custom User model introduced in django 1.5. Do not forget to define `PYBB_PROFILE_RELATED_NAME`
  in settings, if you don't yse predefinet `pybb.PybbProfile` model See :doc:`how to use custom user model
  with pybbm</customuser>`
* Dropped support for django 1.3

0.12.4 -> 0.12.5
----------------

* More flexible forms/forms fields rendering in templates
  Strongly recommended to check rendering of pybbm forms on your site (edit profile, poll/topic create/edit)
* Additional template for markitup preview
  You can override `pybb/_markitup_preview.html` to provide your styling for <code>, <pre> and other markitup tags
* Improved permissions handling see `PYBB_PERMISSION_HANDLER` setting in :doc:`settings</settings>`
* Fixed bugs and improved performance

0.12.3 -> 0.12.4
----------------

* `PYBB_USE_DJANGO_MAILER` setting

0.12.2 -> 0.12.3
----------------

* German translation

0.11 -> 0.12
------------

* Fixed bug when the answers to poll unexpectedly deleted. Strongly recommendet to update to this version, if using
  polls subsystem

* Polish translation


0.10 -> 0.11
------------

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
