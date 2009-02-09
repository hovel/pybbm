from django.utils import translation

class PybbMiddleware(object):
    def process_request(self, request):
        if request.user.is_authenticated():
            profile = request.user.pybb_profile
            language = translation.get_language_from_request(request)

            if not profile.language:
                profile.language = language
                profile.save()
                #print 'Just now set profile language', profile.language

            if profile.language and profile.language != language:
                request.session['django_language'] = profile.language
                translation.activate(profile.language)
                request.LANGUAGE_CODE = translation.get_language()
                #print 'Setuping request language', profile.language
