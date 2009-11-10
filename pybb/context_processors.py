from urlparse import urljoin

from django.conf import settings

def pybb(request):

    media_url = urljoin(settings.MEDIA_URL, 'pybb/')
    skin_media_url = urljoin(media_url, 'skin/%s/' % settings.PYBB_SKIN)

    return {'PYBB_HEADER': settings.PYBB_HEADER,
            'PYBB_TAGLINE': settings.PYBB_TAGLINE,
            'PYBB_NOTICE': settings.PYBB_NOTICE,
            'PYBB_MEDIA_URL': media_url,
            'PYBB_SKIN_MEDIA_URL': skin_media_url,
            }
