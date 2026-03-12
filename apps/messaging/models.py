from django.db import models
from django.conf import settings


class Conversation(models.Model):
    """
    Private conversation between users.
    Mirrors Moodle's mdl_messages_conversations.
    """
    TYPE_INDIVIDUAL = 1
    TYPE_GROUP = 2

    TYPE_CHOICES = [
        (TYPE_INDIVIDUAL, 'Individual'),
        (TYPE_GROUP, 'Group'),
    ]

    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='conversations', through='ConversationMember'
    )
    name = models.CharField(max_length=255, blank=True)
    conv_type = models.IntegerField(choices=TYPE_CHOICES, default=TYPE_INDIVIDUAL)
    image = models.ImageField(upload_to='conversation_images/', blank=True, null=True)
    component = models.CharField(max_length=100, blank=True)
    item_type = models.IntegerField(null=True, blank=True)
    item_id = models.IntegerField(null=True, blank=True)
    context_id = models.IntegerField(null=True, blank=True)
    enabled = models.BooleanField(default=True)
    muted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'elening_conversations'
        ordering = ['-updated_at']

    def __str__(self):
        if self.name:
            return self.name
        members = self.members.select_related('user').all()[:3]
        return ', '.join(str(m.user) for m in members)

    def get_last_message(self):
        return self.messages.order_by('-created_at').first()


class ConversationMember(models.Model):
    """Member of a conversation."""
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name='members'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversation_memberships'
    )
    last_read = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'elening_conversation_members'
        unique_together = ('conversation', 'user')

    def __str__(self):
        return f'{self.user} in {self.conversation}'


class Message(models.Model):
    """
    A message in a conversation.
    Mirrors Moodle's mdl_messages.
    """
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages'
    )
    subject = models.CharField(max_length=255, blank=True)
    full_message = models.TextField()
    full_message_html = models.TextField(blank=True)
    full_message_format = models.IntegerField(default=1)
    small_message = models.TextField(blank=True)
    notification = models.BooleanField(default=False)
    context_url = models.URLField(blank=True)
    context_url_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_by_sender = models.BooleanField(default=False)
    custom_data = models.TextField(blank=True)

    class Meta:
        db_table = 'elening_messages'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender} → {self.conversation}: {self.small_message[:50]}'


class MessageRead(models.Model):
    """Tracks which messages a user has read."""
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name='reads'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='message_reads'
    )
    read_at = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'elening_message_reads'
        unique_together = ('message', 'user')
