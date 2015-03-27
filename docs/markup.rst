Markup
======

How it works
------------

Every time user save new post, message parsed by markup parser to it's html representation.
It will include only allowed by engine html tags, html tags should be html-encoded and rendered
as simple text to prevent XSS attacks.

Pybbm includes two default engines. Actions needed to use these engines:

    - bbcode engine: install required package with ``pip install bbcode`` command and set :ref:`PYBB_MARKUP` to ``'bbcode'``
    - markdown engine: install required package with ``pip install markdown`` command and set :ref:`PYBB_MARKUP` to ``'markdown'``

Engine classes must inherit from `pybb.markup.base.BaseParser` 
which defines three required methods:

    - ``def format(self, text)`` method receives post's text as parameter and returns parsed message as html fragment
    - ``def quote(self, text, username='')`` method receives quoted post's text and username and returns quoted string
      in terms of markup engine
    - ``def get_widget_cls(cls)`` class method which return the class to use as the widget 
      for the body field

How to change
-------------

If you want to write your custom engine you can write a new class which extends ``pybb.markup.base.BaseParser``

To change behavior of one of the default parsers you can override ``pybb.markup.bbcode.BBCodeParser`` or
``pybb.markup.markdown.MarkdownParser``.

For example, for adding additional formatter to bbcode parser you can write your own class in myproject.markup_engines.py::

    from pybb.markup.bbcode import BBCodeParser

    class CustomBBCodeParser(BBCodeParser):
        def __init__(self):
            super(CustomBBCodeParser, self).__init__()
            self._parser.add_simple_formatter('ul', '<ul>%(value)s</ul>', transform_newlines=False, strip=True)
            self._parser.add_simple_formatter('li', '<li>%(value)s</li>', transform_newlines=False, strip=True)


include it in :ref:`PYBB_MARKUP_ENGINES_PATHS` setting dict and point pybbm to use it by :ref:`PYBB_MARKUP` setting::

    PYBB_MARKUP_ENGINES_PATHS = {'custom_bbcode': 'myproject.markup_engines.CustomBBCodeParser'}
    PYBB_MARKUP = 'custom_bbcode'

or you can override default bbcode engine in settings.py::

    PYBB_MARKUP_ENGINES_PATHS = {'bbcode': 'myproject.markup_engines.CustomBBCodeParser'}
    PYBB_MARKUP = 'bbcode' # don't required because 'bbcode' is default value

Using different media assets
----------------------------

When you define your custom markup parser you may want to control how it will be rendered.
For that purpose pybbm uses django's concept of `widgets <https://docs.djangoproject.com/en/1.7/ref/forms/widgets/>`_
and their `media assets <https://docs.djangoproject.com/en/1.7/topics/forms/media/>`_.
Widget class used by markup engine controlled by ``get_widget_cls`` class method of engine class.
By default it returns ``widget_class`` attribute value. Pybbm default parsers use next widgets:

    - pybb.base.BaseParser - django.forms.Textarea
    - pybb.bbcode.BBCodeParser - pybb.bbcode.BBCodeWidget
    - pybb.bbcode.MarkdownParser - pybb.markdown.MarkdownWidget

To get it working in your templates include ``{{ form.media }}`` or ``{{ form.media.css }}`` / ``{{ form.media.js }}``
in proper place in every template where you use post form.
