from django.db import connection
from django.conf import settings

from debug.utils import JsonResponse, decode_entities

def explain_query(request):
    if settings.DEBUG and request.META.get('REMOTE_ADDR') in settings.INTERNAL_IPS:
        query = request.POST['query']
        query = decode_entities(query)

        # super dirty hack, without it django dies with exception
        # tuple index out of range
        # /usr/lib/python2.4/site-packages/django/db/backends/util.py, line 18
        query = query.replace('%', '%%')

        cursor = connection.cursor()
        cursor.execute(u'EXPLAIN %s' % query)

        rows = list(cursor.fetchall())
        if cursor.cursor.description:
            rows.insert(0, [x[0] for x in cursor.cursor.description])
    else:
        rows = (['Access denied'],
                ['You IP %s is not in settings.INTERNAL_IPS' % request.META.get('REMOTE_ADDR', 'N/A')]
                )
        query = ''
    return JsonResponse({'query': query,
                         'explain_rows': rows})
