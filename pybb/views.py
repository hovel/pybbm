# -*- coding: utf-8 -*-

import math

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.db.models import F, Q
from django.db.models.aggregates import Count
from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseBadRequest,\
    HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic.edit import ModelFormMixin
from django.views.decorators.csrf import csrf_protect
from django.views import generic
from pybb.util import build_cache_key

try:
    from pure_pagination import Paginator
except ImportError:
    # the simplest emulation of django-pure-pagination behavior
    from django.core.paginator import Paginator, Page
    class PageRepr(int):
        def querystring(self):
            return 'page=%s' % self
    Page.pages = lambda self: [PageRepr(i) for i in range(1, self.paginator.num_pages + 1)]

from pybb.models import Category, Forum, Topic, Post, TopicReadTracker, ForumReadTracker, PollAnswerUser
from pybb.forms import PostForm, AdminPostForm, AttachmentFormSet, PollAnswerFormSet, PollForm
from pybb.templatetags.pybb_tags import pybb_topic_poll_not_voted
from pybb import defaults

from pybb.permissions import perms

from pybb import util
User = util.get_user_model()
username_field = util.get_username_field()

class RedirectToLoginMixin(object):
    """ mixin which redirects to settings.LOGIN_URL if the view encounters an PermissionDenied exception
        and the user is not authenticated. Views inheriting from this need to implement
        get_login_redirect_url(), which returns the URL to redirect to after login (parameter "next")
    """
    def dispatch(self, request, *args, **kwargs):
        try:
            return super(RedirectToLoginMixin, self).dispatch(request, *args, **kwargs)
        except PermissionDenied:
            if not request.user.is_authenticated():
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(self.get_login_redirect_url())
            else:
                return HttpResponseForbidden()

    def get_login_redirect_url(self):
        """ get the url to which we redirect after the user logs in. subclasses should override this """
        return '/'


class IndexView(generic.ListView):

    template_name = 'pybb/index.html'
    context_object_name = 'categories'

    def get_context_data(self, **kwargs):
        ctx = super(IndexView, self).get_context_data(**kwargs)
        categories = ctx['categories']
        for category in categories:
            category.forums_accessed = perms.filter_forums(self.request.user, category.forums.all())
        ctx['categories'] = categories
        return ctx

    def get_queryset(self):
        return perms.filter_categories(self.request.user, Category.objects.all())


class CategoryView(RedirectToLoginMixin, generic.DetailView):

    template_name = 'pybb/index.html'
    context_object_name = 'category'

    def get_login_redirect_url(self):
        return reverse('pybb:category', args=(self.kwargs['pk'],))

    def get_queryset(self):
        return Category.objects.all()

    def get_object(self, queryset=None):
        obj = super(CategoryView, self).get_object(queryset)
        if not perms.may_view_category(self.request.user, obj):
            raise PermissionDenied
        return obj

    def get_context_data(self, **kwargs):
        ctx = super(CategoryView, self).get_context_data(**kwargs)
        ctx['category'].forums_accessed = perms.filter_forums(self.request.user, ctx['category'].forums.all())
        ctx['categories'] = [ctx['category']]
        return ctx


class ForumView(RedirectToLoginMixin, generic.ListView):

    paginate_by = defaults.PYBB_FORUM_PAGE_SIZE
    context_object_name = 'topic_list'
    template_name = 'pybb/forum.html'
    paginator_class = Paginator

    def get_login_redirect_url(self):
        return reverse('pybb:forum', args=(self.kwargs['pk'],))

    def get_context_data(self, **kwargs):
        ctx = super(ForumView, self).get_context_data(**kwargs)
        ctx['forum'] = self.forum
        return ctx

    def get_queryset(self):
        self.forum = get_object_or_404(Forum.objects.all(), pk=self.kwargs['pk'])
        if not perms.may_view_forum(self.request.user, self.forum):
            raise PermissionDenied

        qs = self.forum.topics.order_by('-sticky', '-updated').select_related()
        qs = perms.filter_topics(self.request.user, qs)
        return qs


class LatestTopicsView(generic.ListView):

    paginate_by = defaults.PYBB_FORUM_PAGE_SIZE
    context_object_name = 'topic_list'
    template_name = 'pybb/latest_topics.html'
    paginator_class = Paginator

    def get_queryset(self):
        qs = Topic.objects.all().select_related()
        qs = perms.filter_topics(self.request.user, qs)
        return qs.order_by('-updated')


class TopicView(RedirectToLoginMixin, generic.ListView):
    paginate_by = defaults.PYBB_TOPIC_PAGE_SIZE
    template_object_name = 'post_list'
    template_name = 'pybb/topic.html'
    paginator_class = Paginator

    def get_login_redirect_url(self):
        return reverse('pybb:topic', args=(self.kwargs['pk'],))

    def dispatch(self, request, *args, **kwargs):
        self.topic = get_object_or_404(Topic.objects.select_related('forum'), pk=kwargs['pk'])

        if request.GET.get('first-unread'):
            if request.user.is_authenticated():
                read_dates = []
                try:
                    read_dates.append(TopicReadTracker.objects.get(user=request.user, topic=self.topic).time_stamp)
                except TopicReadTracker.DoesNotExist:
                    pass
                try:
                    read_dates.append(ForumReadTracker.objects.get(user=request.user, forum=self.topic.forum).time_stamp)
                except ForumReadTracker.DoesNotExist:
                    pass

                read_date = read_dates and max(read_dates)
                if read_date:
                    try:
                        first_unread_topic = self.topic.posts.filter(created__gt=read_date).order_by('created')[0]
                    except IndexError:
                        first_unread_topic = self.topic.last_post
                else:
                    first_unread_topic = self.topic.head
                return HttpResponseRedirect(reverse('pybb:post', kwargs={'pk': first_unread_topic.id}))

        return super(TopicView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if not perms.may_view_topic(self.request.user, self.topic):
            raise PermissionDenied
        if self.request.user.is_authenticated() or not defaults.PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER:
            Topic.objects.filter(id=self.topic.id).update(views=F('views') + 1)
        else:
            cache_key = build_cache_key('anonymous_topic_views', topic_id=self.topic.id)
            cache.add(cache_key, 0)
            if cache.incr(cache_key) % defaults.PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER == 0:
                Topic.objects.filter(id=self.topic.id).update(views=F('views') +
                                                                    defaults.PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER)
                cache.set(cache_key, 0)
        qs = self.topic.posts.all().select_related('user')
        if defaults.PYBB_PROFILE_RELATED_NAME:
            qs = qs.select_related('user__%s' % defaults.PYBB_PROFILE_RELATED_NAME)
        if not perms.may_moderate_topic(self.request.user, self.topic):
            qs = perms.filter_posts(self.request.user, qs)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super(TopicView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated():
            self.request.user.is_moderator = perms.may_moderate_topic(self.request.user, self.topic)
            self.request.user.is_subscribed = self.request.user in self.topic.subscribers.all()
            if perms.may_post_as_admin(self.request.user):
                ctx['form'] = AdminPostForm(initial={'login': getattr(self.request.user, username_field)},
                                            topic=self.topic)
            else:
                ctx['form'] = PostForm(topic=self.topic)
            self.mark_read(self.request, self.topic)
        elif defaults.PYBB_ENABLE_ANONYMOUS_POST:
            ctx['form'] = PostForm(topic=self.topic)
        else:
            ctx['form'] = None
        if defaults.PYBB_ATTACHMENT_ENABLE:
            aformset = AttachmentFormSet()
            ctx['aformset'] = aformset
        if defaults.PYBB_FREEZE_FIRST_POST:
            ctx['first_post'] = self.topic.head
        else:
            ctx['first_post'] = None
        ctx['topic'] = self.topic

        if self.request.user.is_authenticated() and self.topic.poll_type != Topic.POLL_TYPE_NONE and \
           pybb_topic_poll_not_voted(self.topic, self.request.user):
            ctx['poll_form'] = PollForm(self.topic)

        return ctx

    def mark_read(self, request, topic):
        try:
            forum_mark = ForumReadTracker.objects.get(forum=topic.forum, user=request.user)
        except ObjectDoesNotExist:
            forum_mark = None
        if (forum_mark is None) or (forum_mark.time_stamp < topic.updated):
            # Mark topic as readed
            topic_mark, new = TopicReadTracker.objects.get_or_create_tracker(topic=topic, user=request.user)
            if not new:
                topic_mark.save()

            # Check, if there are any unread topics in forum
            read = Topic.objects.filter(Q(forum=topic.forum) & (Q(topicreadtracker__user=request.user,
                                                                  topicreadtracker__time_stamp__gt=F('updated'))) |
                                                                Q(forum__forumreadtracker__user=request.user,
                                                                  forum__forumreadtracker__time_stamp__gt=F('updated')))
            unread = Topic.objects.filter(forum=topic.forum).exclude(id__in=read)
            if not unread.exists():
                # Clear all topic marks for this forum, mark forum as readed
                TopicReadTracker.objects.filter(user=request.user, topic__forum=topic.forum).delete()
                forum_mark, new = ForumReadTracker.objects.get_or_create_tracker(forum=topic.forum, user=request.user)
                forum_mark.save()


class PostEditMixin(object):

    def get_form_class(self):
        if perms.may_post_as_admin(self.request.user):
            return AdminPostForm
        else:
            return PostForm

    def get_context_data(self, **kwargs):
        ctx = super(PostEditMixin, self).get_context_data(**kwargs)
        if defaults.PYBB_ATTACHMENT_ENABLE and (not 'aformset' in kwargs):
            ctx['aformset'] = AttachmentFormSet(instance=self.object if getattr(self, 'object') else None)
        if 'pollformset' not in kwargs:
            ctx['pollformset'] = PollAnswerFormSet(instance=self.object.topic if getattr(self, 'object') else None)
        return ctx

    def form_valid(self, form):
        success = True
        save_attachments = False
        save_poll_answers = False
        self.object = form.save(commit=False)

        if defaults.PYBB_ATTACHMENT_ENABLE:
            aformset = AttachmentFormSet(self.request.POST, self.request.FILES, instance=self.object)
            if aformset.is_valid():
                save_attachments = True
            else:
                success = False
        else:
            aformset = AttachmentFormSet()

        pollformset = PollAnswerFormSet()
        if getattr(self, 'forum', None) or self.object.topic.head == self.object:
            if self.object.topic.poll_type != Topic.POLL_TYPE_NONE:
                pollformset = PollAnswerFormSet(self.request.POST, instance=self.object.topic)
                if pollformset.is_valid():
                    save_poll_answers = True
                else:
                    success = False
            else:
                self.object.topic.poll_question = None
                self.object.topic.poll_answers.all().delete()

        if success:
            self.object.topic.save()
            self.object.topic = self.object.topic
            self.object.save()
            if save_attachments:
                aformset.save()
            if save_poll_answers:
                pollformset.save()
            return super(ModelFormMixin, self).form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form, aformset=aformset, pollformset=pollformset))


class AddPostView(PostEditMixin, generic.CreateView):

    template_name = 'pybb/add_post.html'

    def get_form_kwargs(self):
        ip = self.request.META.get('REMOTE_ADDR', '')
        form_kwargs = super(AddPostView, self).get_form_kwargs()
        form_kwargs.update(dict(topic=self.topic, forum=self.forum, user=self.user,
                       ip=ip, initial={}))
        if 'quote_id' in self.request.GET:
            try:
                quote_id = int(self.request.GET.get('quote_id'))
            except TypeError:
                raise Http404
            else:
                post = get_object_or_404(Post, pk=quote_id)
                quote = defaults.PYBB_QUOTE_ENGINES[defaults.PYBB_MARKUP](post.body, getattr(post.user, username_field))
                form_kwargs['initial']['body'] = quote
        if self.user.is_staff:
            form_kwargs['initial']['login'] = getattr(self.user, username_field)
        return form_kwargs

    def get_context_data(self, **kwargs):
        ctx = super(AddPostView, self).get_context_data(**kwargs)
        ctx['forum'] = self.forum
        ctx['topic'] = self.topic
        return ctx

    def get_success_url(self):
        if (not self.request.user.is_authenticated()) and defaults.PYBB_PREMODERATION:
            return reverse('pybb:index')
        return super(AddPostView, self).get_success_url()

    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            self.user = request.user
        else:
            if defaults.PYBB_ENABLE_ANONYMOUS_POST:
                self.user, new = User.objects.get_or_create(**{username_field: defaults.PYBB_ANONYMOUS_USERNAME})
            else:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())

        self.forum = None
        self.topic = None
        if 'forum_id' in kwargs:
            self.forum = get_object_or_404(perms.filter_forums(request.user, Forum.objects.all()), pk=kwargs['forum_id'])
            if not perms.may_create_topic(self.user, self.forum):
                raise PermissionDenied
        elif 'topic_id' in kwargs:
            self.topic = get_object_or_404(perms.filter_topics(request.user, Topic.objects.all()), pk=kwargs['topic_id'])
            if not perms.may_create_post(self.user, self.topic):
                raise PermissionDenied
        return super(AddPostView, self).dispatch(request, *args, **kwargs)


class EditPostView(PostEditMixin, generic.UpdateView):

    model = Post

    context_object_name = 'post'
    template_name = 'pybb/edit_post.html'

    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        return super(EditPostView, self).dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        post = super(EditPostView, self).get_object(queryset)
        if not perms.may_edit_post(self.request.user, post):
            raise PermissionDenied
        return post


class UserView(generic.DetailView):
    model = User
    template_name = 'pybb/user.html'
    context_object_name = 'target_user'

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, **{username_field: self.kwargs['username']})

    def get_context_data(self, **kwargs):
        ctx = super(UserView, self).get_context_data(**kwargs)
        ctx['topic_count'] = Topic.objects.filter(user=ctx['target_user']).count()
        return ctx


class UserPosts(generic.ListView):
    model = Post
    paginate_by = defaults.PYBB_TOPIC_PAGE_SIZE
    paginator_class = Paginator
    template_name = 'pybb/user_posts.html'

    def dispatch(self, request, *args, **kwargs):
        username = kwargs.pop('username')
        self.user = get_object_or_404(**{'klass': User, username_field: username})
        return super(UserPosts, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super(UserPosts, self).get_queryset()
        qs = qs.filter(user=self.user)
        qs = perms.filter_posts(self.request.user, qs).select_related('topic')
        qs = qs.order_by('-created', '-updated')
        return qs

    def get_context_data(self, **kwargs):
        context = super(UserPosts, self).get_context_data(**kwargs)
        context['target_user'] = self.user
        return context


class UserTopics(generic.ListView):
    model = Topic
    paginate_by = defaults.PYBB_FORUM_PAGE_SIZE
    paginator_class = Paginator
    template_name = 'pybb/user_topics.html'

    def dispatch(self, request, *args, **kwargs):
        username = kwargs.pop('username')
        self.user = get_object_or_404(User, username=username)
        return super(UserTopics, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super(UserTopics, self).get_queryset()
        qs = qs.filter(user=self.user)
        qs = perms.filter_topics(self.user, qs)
        qs = qs.order_by('-updated', '-created')
        return qs

    def get_context_data(self, **kwargs):
        context = super(UserTopics, self).get_context_data(**kwargs)
        context['target_user'] = self.user
        return context


class PostView(RedirectToLoginMixin, generic.RedirectView):

    def get_login_redirect_url(self):
        return reverse('pybb:post', args=(self.kwargs['pk'],))

    def get_redirect_url(self, **kwargs):
        post = get_object_or_404(Post.objects.all(), pk=self.kwargs['pk'])
        if not perms.may_view_post(self.request.user, post):
            raise PermissionDenied
        count = post.topic.posts.filter(created__lt=post.created).count() + 1
        page = math.ceil(count / float(defaults.PYBB_TOPIC_PAGE_SIZE))
        return '%s?page=%d#post-%d' % (reverse('pybb:topic', args=[post.topic.id]), page, post.id)


class ModeratePost(generic.RedirectView):
    def get_redirect_url(self, **kwargs):
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        if not perms.may_moderate_topic(self.request.user, post.topic):
            raise PermissionDenied
        post.on_moderation = False
        post.save()
        return post.get_absolute_url()


class ProfileEditView(generic.UpdateView):

    template_name = 'pybb/edit_profile.html'

    def get_object(self, queryset=None):
        return util.get_pybb_profile(self.request.user)

    def get_form_class(self):
        if not self.form_class:
            from pybb.forms import EditProfileForm
            return EditProfileForm
        else:
            return super(ProfileEditView, self).get_form_class()

    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        return super(ProfileEditView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('pybb:edit_profile')


class DeletePostView(generic.DeleteView):

    template_name = 'pybb/delete_post.html'
    context_object_name = 'post'

    def get_object(self, queryset=None):
        post = get_object_or_404(Post.objects.select_related('topic', 'topic__forum'), pk=self.kwargs['pk'])
        if not perms.may_delete_post(self.request.user, post):
            raise PermissionDenied
        self.topic = post.topic
        self.forum = post.topic.forum
        if not perms.may_moderate_topic(self.request.user, self.topic):
            raise PermissionDenied
        return post

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        redirect_url = self.get_success_url()
        if not request.is_ajax():
            return HttpResponseRedirect(redirect_url)
        else:
            return HttpResponse(redirect_url)

    def get_success_url(self):
        try:
            Topic.objects.get(pk=self.topic.id)
        except Topic.DoesNotExist:
            return self.forum.get_absolute_url()
        else:
            if not self.request.is_ajax():
                return self.topic.get_absolute_url()
            else:
                return ""


class TopicActionBaseView(generic.View):

    def get_topic(self):
        return get_object_or_404(Topic, pk=self.kwargs['pk'])

    @method_decorator(login_required)
    def get(self, *args, **kwargs):
        self.topic = self.get_topic()
        self.action(self.topic)
        return HttpResponseRedirect(self.topic.get_absolute_url())


class StickTopicView(TopicActionBaseView):

    def action(self, topic):
        if not perms.may_stick_topic(self.request.user, topic):
            raise PermissionDenied
        topic.sticky = True
        topic.save()


class UnstickTopicView(TopicActionBaseView):

    def action(self, topic):
        if not perms.may_unstick_topic(self.request.user, topic):
            raise PermissionDenied
        topic.sticky = False
        topic.save()


class CloseTopicView(TopicActionBaseView):

    def action(self, topic):
        if not perms.may_close_topic(self.request.user, topic):
            raise PermissionDenied
        topic.closed = True
        topic.save()


class OpenTopicView(TopicActionBaseView):
    def action(self, topic):
        if not perms.may_open_topic(self.request.user, topic):
            raise PermissionDenied
        topic.closed = False
        topic.save()


class TopicPollVoteView(generic.UpdateView):
    model = Topic
    http_method_names = ['post', ]
    form_class = PollForm

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(TopicPollVoteView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(ModelFormMixin, self).get_form_kwargs()
        kwargs['topic'] = self.object
        return kwargs

    def form_valid(self, form):
        # already voted
        if not pybb_topic_poll_not_voted(self.object, self.request.user):
            return HttpResponseForbidden()

        answers = form.cleaned_data['answers']
        for answer in answers:
            # poll answer from another topic
            if answer.topic != self.object:
                return HttpResponseBadRequest()

            PollAnswerUser.objects.create(poll_answer=answer, user=self.request.user)
        return super(ModelFormMixin, self).form_valid(form)

    def form_invalid(self, form):
        return redirect(self.object)

    def get_success_url(self):
        return self.object.get_absolute_url()


@login_required
def topic_cancel_poll_vote(request, pk):
    topic = get_object_or_404(Topic, pk=pk)
    PollAnswerUser.objects.filter(user=request.user, poll_answer__topic_id=topic.id).delete()
    return HttpResponseRedirect(topic.get_absolute_url())


@login_required
def delete_subscription(request, topic_id):
    topic = get_object_or_404(perms.filter_topics(request.user, Topic.objects.all()), pk=topic_id)
    topic.subscribers.remove(request.user)
    return HttpResponseRedirect(topic.get_absolute_url())


@login_required
def add_subscription(request, topic_id):
    topic = get_object_or_404(perms.filter_topics(request.user, Topic.objects.all()), pk=topic_id)
    topic.subscribers.add(request.user)
    return HttpResponseRedirect(topic.get_absolute_url())


@login_required
def post_ajax_preview(request):
    content = request.POST.get('data')
    html = defaults.PYBB_MARKUP_ENGINES[defaults.PYBB_MARKUP](content)
    return render(request, 'pybb/_markitup_preview.html', {'html': html})


@login_required
def mark_all_as_read(request):
    for forum in perms.filter_forums(request.user, Forum.objects.all()):
        forum_mark, new = ForumReadTracker.objects.get_or_create_tracker(forum=forum, user=request.user)
        forum_mark.save()
    TopicReadTracker.objects.filter(user=request.user).delete()
    msg = _('All forums marked as read')
    messages.success(request, msg, fail_silently=True)
    return redirect(reverse('pybb:index'))


@login_required
@require_POST
def block_user(request, username):
    user = get_object_or_404(User, **{username_field: username})
    if not perms.may_block_user(request.user, user):
        raise PermissionDenied
    user.is_active = False
    user.save()
    if 'block_and_delete_messages' in request.POST:
        # individually delete each post and empty topic to fire method
        # with forum/topic counters recalculation
        for p in Post.objects.filter(user=user):
            p.delete()
        for t in Topic.objects.annotate(cnt=Count('posts')).filter(cnt=0):
            t.delete()
    msg = _('User successfuly blocked')
    messages.success(request, msg, fail_silently=True)
    return redirect('pybb:index')
