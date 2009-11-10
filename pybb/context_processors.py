from django.conf import settings

def pybb(request):
    context = {}
    for key in settings.get_all_members():
        if key.startswith('PYBB_'):
            context[key] = getattr(settings, key)
    return context

