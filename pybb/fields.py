"""
Details about AutoOneToOneField:
    http://softwaremaniacs.org/blog/2007/03/07/auto-one-to-one-field/
"""

from django.db.models import OneToOneField
from django.db.models.fields.related import SingleRelatedObjectDescriptor 
from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson


class AutoSingleRelatedObjectDescriptor(SingleRelatedObjectDescriptor):
    def __get__(self, instance, instance_type=None):
        try:
            return super(AutoSingleRelatedObjectDescriptor, self).__get__(instance, instance_type)
        except self.related.model.DoesNotExist:
            obj = self.related.model(**{self.related.field.name: instance})
            obj.save()
            return obj


class AutoOneToOneField(OneToOneField):
    """
    OneToOneField creates dependent object on first request from parent object
    if dependent oject has not created yet.
    """

    def contribute_to_related_class(self, cls, related):
        setattr(cls, related.get_accessor_name(), AutoSingleRelatedObjectDescriptor(related))


class JSONField(models.TextField):
    """
    JSONField is a generic textfield that neatly serializes/unserializes
    JSON objects seamlessly.
    Django snippet #1478
    """

    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if value == "":
            return None

        try:
            if isinstance(value, basestring):
                return simplejson.loads(value)
        except ValueError:
            pass
        return value

    def get_db_prep_save(self, value):
        if value == "":
            return None
        if isinstance(value, dict):
            value = simplejson.dumps(value, cls=DjangoJSONEncoder)
        return super(JSONField, self).get_db_prep_save(value)
