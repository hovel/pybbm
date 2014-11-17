# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pybb.markup_engines import PARSERS, init_bbcode_parser, bbcode, markdown

init_bbcode_parser()
PARSERS['bbcode'].add_simple_formatter(
    'ul', 
    '<ul>%(value)s</ul>', 
    transform_newlines=False, strip=True)
PARSERS['bbcode'].add_simple_formatter(
    'li', 
    '<li>%(value)s</li>', 
    transform_newlines=False, strip=True)
PARSERS['bbcode'].add_simple_formatter(
    'youtube', 
    (
        '<iframe src="http://www.youtube.com/embed/%(value)s?wmode=opaque" '
        'data-youtube-id="%(value)s" allowfullscreen="" frameborder="0" '
        'height="315" width="560"></iframe>'
    ), 
    replace_links=False,
)

def liberator(s):
    chains_to_freedom = (
        ('Windows', 'GNU Linux'),
        ('Mac OS', 'FreeBSD'),
        ('PHP', 'Python'),
    )
    for r in chains_to_freedom:
        s = s.replace(*r)
    return s
