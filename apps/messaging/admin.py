from django.contrib import admin
from .models import Conversation, ConversationMember, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'conv_type', 'enabled', 'created_at']
    list_filter = ['conv_type', 'enabled']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'conversation', 'small_message', 'notification', 'created_at']
    list_filter = ['notification', 'deleted_by_sender']
    search_fields = ['sender__email', 'full_message']
