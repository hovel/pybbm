# -*- coding: utf-8 -*-
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.core.paginator import ObjectPaginator
from django.db.models import FieldDoesNotExist

from common.decorators import paged, render_to
from common.forms import build_form
import flash

#__all__ = ['edit_list', 'create_object', 'edit_object', 'show_object']

def edit_list(qset, paginate_by=10000, create_view=None, extra_fields=None,
              filter_form_class=None, per_page_var='per_page'): 
    """
    Generate view for displaing list object with pagination, edit links and
    create new link.
    """

    @render_to('common/edit_list.html')
    def view(request):
        # I hate this featurebug :-/
        qs = qset
        if filter_form_class:
            filter_form = filter_form_class(request.GET)
            filter_form.is_valid()
            qs = filter_form.filter(qs)
        else:
            filter_form = None

        try:
            page = int(request.GET.get('page', 1))
        except ValueError:
            page = 1

        real_per_page = paginate_by

        if per_page_var:
            try:
                value = int(request.GET[per_page_var])
            except (ValueError, KeyError):
                pass
            else:
                if value > 0:
                    real_per_page = value

        paginator = ObjectPaginator(qs, real_per_page)
        objects = paginator.get_page(page - 1)

        headers = []
        headers.append(qs.model._meta.verbose_name)

        if extra_fields:
            objects = list(objects)
            for obj in objects:
                obj.extra__ = []
                add_headers = []
                for key in extra_fields:
                    field = getattr(obj, key)
                    if callable(field):
                        field_value = field()
                    else:
                        field_value = field
                    obj.extra__.append(field_value)
                    try:
                        name = obj._meta.get_field(key).verbose_name
                    except FieldDoesNotExist:
                        name = getattr(field, 'verbose_name', key)
                    add_headers.append(name)
            headers.extend(add_headers)

        model = qs.model
        
        try:
            new_name = model.Labels.new_name 
        except AttributeError:
            new_name = u'Новый объект'

        return {'objects': objects,
                'page': page,
                'pages': paginator.pages,
                'create_url': getattr(model, 'get_create_url', lambda: None)(),
                'list_url': getattr(model, 'get_list_url', lambda: None)(),
                'verbose_name': model._meta.verbose_name,
                'verbose_name_plural': model._meta.verbose_name_plural,
                'new_name': new_name,
                'filter_form': filter_form,
                'headers': headers,
                'per_page': real_per_page,
                'per_page_all': paginate_by,
                }
    return view


def create_object(model, form_class, redirect=lambda x: x.get_list_url()):
    """
    Generate view for creating new object with given form class.
    """

    @render_to('common/create_object.html')
    def view(request):
        form = build_form(form_class, request)
        if form.is_valid():
            obj = form.save()
            flash.notice_next(u'Объект создан')
            return HttpResponseRedirect(redirect(obj))
        
        try:
            new_name = model.Labels.new_name 
        except AttributeError:
            new_name = u'Новый объект'

        return {'form': form,
                'verbose_name': model._meta.verbose_name,
                'verbose_name_plural': model._meta.verbose_name_plural,
                'list_url': getattr(model, 'get_list_url', lambda: None)(),
                'new_name': new_name,
                }
    return view


def edit_object(model, form_class, template_name='common/edit_object.html', redirect=lambda x: x.get_list_url()):
    """
    Generate view for editing object with given form class.
    """

    @render_to(template_name)
    def view(request, object_id):
        object = get_object_or_404(model, pk=object_id)
        form = build_form(form_class, request, instance=object)
        if form.is_valid():
            object = form.save()
            flash.notice_next(u'Данные сохранены')
            return HttpResponseRedirect(redirect(object))

        return {'form': form,
                'verbose_name': model._meta.verbose_name,
                'verbose_name_plural': model._meta.verbose_name_plural,
                'object': object,
                'list_url': getattr(model, 'get_list_url', lambda: None)(),
                }
    return view


def show_object(model, template_name):
    """
    Genereate view for displaying object properties with given
    template.
    """

    @render_to(template_name)
    def view(request, object_id):
        object = get_object_or_404(model, pk=object_id)
        return {'object': object}
    return view
