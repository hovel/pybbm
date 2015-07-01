from pybb.models.attachment import Attachment
from pybb.models.category import Category
from pybb.models.forum import Forum
from pybb.models.post import Post
from pybb.models.profile import PybbProfile, Profile
from pybb.models.read_trackers import ForumReadTracker, TopicReadTracker
from pybb.models.renderable import RenderableItem
from pybb.models.topic import Topic, PollAnswer, PollAnswerUser

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from pybb.compat import slugify
from pybb import defaults


try:
    from south.modelsinspector import add_introspection_rules

    add_introspection_rules([], ["^annoying\.fields\.JSONField"])
    add_introspection_rules([], ["^annoying\.fields\.AutoOneToOneField"])
except ImportError:
    pass


def create_or_check_slug(instance, model, **extra_filters):
    """
    returns a unique slug

    :param instance : target instance
    :param model: needed as instance._meta.model is available since django 1.6
    :param extra_filters: filters needed for Forum and Topic for their unique_together field
    """
    initial_slug = instance.slug or slugify(instance.name)
    count = -1
    last_count_len = 0
    slug_is_not_unique = True
    while slug_is_not_unique:
        count += 1

        if count >= defaults.PYBB_NICE_URL_SLUG_DUPLICATE_LIMIT:
            msg = _('After %(limit)s attemps, there is not any unique slug value for "%(slug)s"')
            raise ValidationError(msg % {'limit': defaults.PYBB_NICE_URL_SLUG_DUPLICATE_LIMIT,
                                         'slug': initial_slug})

        count_len = len(str(count))

        if last_count_len != count_len:
            last_count_len = count_len
            filters = {'slug__startswith': initial_slug[:(254-count_len)], }
            if extra_filters:
                filters.update(extra_filters)
            objs = model.objects.filter(**filters).exclude(pk=instance.pk)
            slug_list = [obj.slug for obj in objs]

        if count == 0:
            slug = initial_slug
        else:
            slug = '%s-%d' % (initial_slug[:(254-count_len)], count)
        slug_is_not_unique = slug in slug_list

    return slug
