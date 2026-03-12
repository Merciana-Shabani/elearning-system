from django.contrib import admin
from .models import Forum, ForumThread, ForumPost, ForumSubscription


class ForumThreadInline(admin.TabularInline):
    model = ForumThread
    extra = 0
    fields = ['name', 'author', 'pinned', 'locked', 'visible']
    show_change_link = True


@admin.register(Forum)
class ForumAdmin(admin.ModelAdmin):
    list_display = ['name', 'course', 'forum_type', 'post_count', 'visible']
    list_filter = ['forum_type', 'visible', 'course']
    search_fields = ['name', 'course__fullname']
    inlines = [ForumThreadInline]


@admin.register(ForumThread)
class ForumThreadAdmin(admin.ModelAdmin):
    list_display = ['name', 'forum', 'author', 'pinned', 'locked', 'visible', 'created_at']
    list_filter = ['pinned', 'locked', 'forum__course']
    search_fields = ['name', 'author__email']


@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    list_display = ['author', 'thread', 'subject', 'deleted', 'created_at']
    list_filter = ['deleted', 'edited']
    search_fields = ['author__email', 'message', 'subject']
