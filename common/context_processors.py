from django.conf import settings

def settings_processor(request):
    """
    Context processor which populates request object with site settings.
    """

    return {'settings': settings}
