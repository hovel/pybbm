"""
Django template loader which loads pybb templates
from correct skin directory.
"""
import os.path

from django.template import TemplateDoesNotExist
from django.template.loaders import filesystem
from django.template.loaders import app_directories
from django.conf import settings


def modify_path(path):
    """
    Insert skin directory name into template path.
    """

    head = path
    chunks = []
    while head:
        head, tail = os.path.split(path)
        chunks.insert(0, tail)
        # Break cycle if we found the root of path
        # I don't know what will happens in windows
        if path == head:
            chunks.insert(0, path)
            break
        path = head

    # Paste skin derectory after pybb directory
    if 'pybb' in chunks:
        index = chunks.index('pybb')
        chunk = os.path.join('skin', settings.PYBB_SKIN)
        chunks.insert(index + 1, chunk)

    return os.path.join(*chunks)


#def get_template_sources(template_name, template_dirs=None):
    #template_name = modify_path(template_name)
    #for x in filesystem.get_template_sources(template_name, template_dirs):
        #yield x


def load_template_source(template_name, template_dirs=None):

    # TODO: use all loaders from settings.TEMPLATE_LOADERS
    # except pybb loader

    template_name = modify_path(template_name)
    try:
        return filesystem.load_template_source(template_name, template_dirs)
    except TemplateDoesNotExist:
        pass
    return app_directories.load_template_source(template_name, template_dirs)


load_template_source.is_usable = True
