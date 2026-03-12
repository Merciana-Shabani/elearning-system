from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages as django_messages
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView
from django.db.models import Q
from .models import Conversation, ConversationMember, Message, MessageRead
from apps.users.models import User


class InboxView(LoginRequiredMixin, ListView):
    template_name = 'messaging/inbox.html'
    context_object_name = 'conversations'

    def get_queryset(self):
        return Conversation.objects.filter(
            members__user=self.request.user,
            enabled=True
        ).order_by('-updated_at').distinct()


@login_required
def conversation_detail(request, pk):
    conversation = get_object_or_404(
        Conversation, pk=pk, members__user=request.user
    )
    msgs = conversation.messages.select_related('sender').order_by('created_at')

    # Mark all as read
    for msg in msgs:
        MessageRead.objects.get_or_create(message=msg, user=request.user)

    if request.method == 'POST':
        text = request.POST.get('message', '').strip()
        if text:
            msg = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                full_message=text,
                small_message=text[:200],
            )
            conversation.save()  # update updated_at
            django_messages.success(request, 'Message sent.')
        return redirect('messaging:conversation', pk=pk)

    return render(request, 'messaging/conversation.html', {
        'conversation': conversation,
        'messages_list': msgs,
    })


@login_required
def new_conversation(request, user_pk):
    other_user = get_object_or_404(User, pk=user_pk)
    if other_user == request.user:
        return redirect('messaging:inbox')

    # Find existing individual conversation between these two users
    existing = Conversation.objects.filter(
        conv_type=Conversation.TYPE_INDIVIDUAL,
        members__user=request.user
    ).filter(
        members__user=other_user
    ).first()

    if existing:
        return redirect('messaging:conversation', pk=existing.pk)

    conversation = Conversation.objects.create(conv_type=Conversation.TYPE_INDIVIDUAL)
    ConversationMember.objects.create(conversation=conversation, user=request.user)
    ConversationMember.objects.create(conversation=conversation, user=other_user)
    return redirect('messaging:conversation', pk=conversation.pk)
