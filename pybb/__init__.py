from django import VERSION

if VERSION[:2] < (1, 7):
    from pybb import signals
    signals.setup()
else:
    default_app_config = 'pybb.apps.PybbConfig'
