from datetime import datetime
import os.path
import random

from django.shortcuts import render_to_response
from django.template import RequestContext

from common.http import HttpResponseJson

def render_to(template_path):
    """
    Expect the dict from view. Render returned dict with
    RequestContext.
    """

    def decorator(func):
        def wrapper(request, *args, **kwargs):
            import pdb
            #output = pdb.runcall(func, request, *args, **kwargs)
            output = func(request, *args, **kwargs)
            if not isinstance(output, dict):
                return output
            kwargs = {'context_instance': RequestContext(request)}
            if 'MIME_TYPE' in output:
                kwargs['mimetype'] = output.pop('MIME_TYPE')
            if 'TEMPLATE' in output:
                template = output.pop('TEMPLATE')
            else:
                template = template_path
            return render_to_response(template, output, **kwargs)
        return wrapper

    return decorator


def paged(paged_list_name, per_page=20, per_page_var='per_page'):
    """
    Parse page from GET data and pass it to view. Split the
    query set returned from view.
    """
    
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            result = func(request, *args, **kwargs)
            if not isinstance(result, dict):
                return result
            try:
                page = int(request.GET.get('page', 1))
            except ValueError:
                page = 1

            real_per_page = per_page

            if per_page_var:
                try:
                    value = int(request.GET[per_page_var])
                except (ValueError, KeyError):
                    pass
                else:
                    if value > 0:
                        real_per_page = value

            from django.core.paginator import Paginator
            paginator = Paginator(result['paged_qs'], real_per_page)
            result[paged_list_name] = paginator.page(page).object_list
            result['page'] = page
            result['pages'] = paginator.num_pages
            result['per_page'] = real_per_page
            return result
        return wrapper

    return decorator


def ajax(view):
    """
    Serialize with JSON the view response.
    """

    def decorated(request, *args, **kwargs):
        data = view(request, *args, **kwargs)
        return HttpResponseJson(data)

    return decorated
