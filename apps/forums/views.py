from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import DetailView, ListView, CreateView
from django.urls import reverse
from .models import Forum, ForumThread, ForumPost
from .forms import ForumThreadForm, ForumPostForm
from apps.enrollment.models import Enrollment


class ForumDetailView(LoginRequiredMixin, DetailView):
    model = Forum
    template_name = 'forums/forum_detail.html'
    context_object_name = 'forum'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['threads'] = self.get_object().threads.filter(
            visible=True
        ).select_related('author').order_by('-pinned', '-updated_at')
        return context


class ThreadDetailView(LoginRequiredMixin, DetailView):
    model = ForumThread
    template_name = 'forums/thread_detail.html'
    context_object_name = 'thread'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thread = self.get_object()
        context['posts'] = thread.posts.filter(
            deleted=False
        ).select_related('author').order_by('created_at')
        context['reply_form'] = ForumPostForm()
        return context


@login_required
def create_thread(request, forum_pk):
    forum = get_object_or_404(Forum, pk=forum_pk)

    if not Enrollment.objects.filter(
        user=request.user, course=forum.course, status='active'
    ).exists() and not request.user.is_staff:
        messages.error(request, 'You must be enrolled to post.')
        return redirect('courses:detail', pk=forum.course.pk)

    if request.method == 'POST':
        thread_form = ForumThreadForm(request.POST)
        post_form = ForumPostForm(request.POST, request.FILES)
        if thread_form.is_valid() and post_form.is_valid():
            thread = thread_form.save(commit=False)
            thread.forum = forum
            thread.author = request.user
            thread.course = forum.course
            thread.save()

            post = post_form.save(commit=False)
            post.thread = thread
            post.author = request.user
            post.subject = thread.name
            post.save()

            messages.success(request, 'Thread created.')
            return redirect('forums:thread', pk=thread.pk)
    else:
        thread_form = ForumThreadForm()
        post_form = ForumPostForm()

    return render(request, 'forums/create_thread.html', {
        'forum': forum,
        'thread_form': thread_form,
        'post_form': post_form,
    })


@login_required
def reply_to_thread(request, thread_pk):
    thread = get_object_or_404(ForumThread, pk=thread_pk, visible=True)

    if thread.locked:
        messages.error(request, 'This thread is locked.')
        return redirect('forums:thread', pk=thread_pk)

    if request.method == 'POST':
        form = ForumPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.thread = thread
            post.author = request.user
            parent_id = request.POST.get('parent_id')
            if parent_id:
                post.parent_id = parent_id
            post.save()

            thread.save()  # Update updated_at
            messages.success(request, 'Reply posted.')
            return redirect('forums:thread', pk=thread_pk)

    return redirect('forums:thread', pk=thread_pk)
