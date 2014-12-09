Markup
======

How it works
------------

Every time user save new post, message parsed by markup parser to it's html representation.
It will include only allowed by engine html tags, html tags should be html-encoded and rendered
as simple text to prevent XSS attacks.

Pybbm includes two default engines. Actions needed to use this engines:

    - bbcode engine: install required package with ``pip install bbcode`` command and set PYBB_MARKUP to ``'bbcode'``
    - markdown engine: install required package with ``pip install markdown`` command and set PYBB_MARKUP to ``'markdown'``

This is class with two required methods:

    - ``def format(self, text)`` method receives post's text as parameter and returns parsed message as html fragment
    - ``def quote(self, text, username='')`` method receives quoted post's text and username and returns quoted string
      in terms of markup engine

How to change
-------------

If you want to write your custom engine you can override ``pybb.markup.base.BaseParser``
or write new class from scratch with required methods above.

To change behavior of one of the default parsers you can override ``pybb.markup.bbcode.BBCodeParser`` or
``pybb.markup.markdown.MarkdownParser``.

For example, for adding additional formatter to bbcode parser you can write your own class in myproject.markup_engines.py::

    from pybb.markup.bbcode import BBCodeParser

    class CustomBBCodeParser(BBCodeParser):
        def __init__(self):
            super(CustomBBCodeParser, self).__init__()
            self._parser.add_simple_formatter('ul', '<ul>%(value)s</ul>', transform_newlines=False, strip=True)
            self._parser.add_simple_formatter('li', '<li>%(value)s</li>', transform_newlines=False, strip=True)


include it in ``PYBB_MARKUP_ENGINES`` setting dict and point pybbm to use it by ``PYBB_MARKUP`` setting::

    PYBB_MARKUP_ENGINES = {'custom_bbcode': 'myproject.markup_engines.CustomBBCodeParser'}
    PYBB_MARKUP = 'custom_bbcode'

or you can override default bbcode engine in settings.py::

    PYBB_MARKUP_ENGINES = {'bbcode': 'myproject.markup_engines.CustomBBCodeParser'}
    PYBB_MARKUP = 'bbcode' # don't required because 'bbcode' is default value

