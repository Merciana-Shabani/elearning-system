from django.db import models
from django.conf import settings
from ckeditor_uploader.fields import RichTextUploadingField


class Forum(models.Model):
    """
    Discussion forum.
    Mirrors Moodle's mdl_forum.
    """
    TYPE_GENERAL = 'general'
    TYPE_NEWS = 'news'
    TYPE_SINGLE = 'single'
    TYPE_QANDA = 'qanda'
    TYPE_BLOG = 'blog'

    TYPE_CHOICES = [
        (TYPE_GENERAL, 'General discussion'),
        (TYPE_NEWS, 'News and announcements'),
        (TYPE_SINGLE, 'Single simple discussion'),
        (TYPE_QANDA, 'Q & A forum'),
        (TYPE_BLOG, 'Blog-like forum'),
    ]

    course = models.ForeignKey(
        'courses.Course', on_delete=models.CASCADE, related_name='forums'
    )
    name = models.CharField(max_length=255)
    forum_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_GENERAL)
    intro = RichTextUploadingField(blank=True)
    assessed = models.IntegerField(default=0)
    scale = models.IntegerField(default=0)
    max_bytes = models.IntegerField(default=0)
    max_attachments = models.IntegerField(default=1)
    force_subscribe = models.IntegerField(default=0)
    tracking_type = models.IntegerField(default=1)
    rss_type = models.IntegerField(default=0)
    rss_articles = models.IntegerField(default=0)
    block_after = models.IntegerField(default=0)
    block_period = models.IntegerField(default=0)
    visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'elening_forums'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.course.shortname})'

    @property
    def post_count(self):
        return ForumPost.objects.filter(thread__forum=self).count()


class ForumThread(models.Model):
    """
    Discussion thread in a forum.
    Mirrors Moodle's mdl_forum_discussions.
    """
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE, related_name='threads')
    name = models.CharField(max_length=255, verbose_name='Subject')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_threads'
    )
    course = models.ForeignKey(
        'courses.Course', on_delete=models.CASCADE, related_name='forum_threads'
    )
    pinned = models.BooleanField(default=False)
    locked = models.BooleanField(default=False)
    visible = models.BooleanField(default=True)
    group_id = models.IntegerField(null=True, blank=True)
    time_start = models.DateTimeField(null=True, blank=True)
    time_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'elening_forum_threads'
        ordering = ['-pinned', '-updated_at']

    def __str__(self):
        return self.name

    @property
    def reply_count(self):
        return self.posts.count() - 1  # Exclude first post


class ForumPost(models.Model):
    """
    A post within a forum thread.
    Mirrors Moodle's mdl_forum_posts.
    """
    thread = models.ForeignKey(ForumThread, on_delete=models.CASCADE, related_name='posts')
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_posts'
    )
    subject = models.CharField(max_length=255, blank=True)
    message = RichTextUploadingField()
    attachment = models.FileField(upload_to='forum_attachments/', blank=True, null=True)
    edited = models.BooleanField(default=False)
    mailed = models.BooleanField(default=False)
    word_count = models.IntegerField(null=True, blank=True)
    deleted = models.BooleanField(default=False)
    private_reply_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='private_replies'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'elening_forum_posts'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author} in "{self.thread.name}"'


class ForumSubscription(models.Model):
    """User subscription to a forum."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_subscriptions'
    )
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE, related_name='subscriptions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'elening_forum_subscriptions'
        unique_together = ('user', 'forum')

    def __str__(self):
        return f'{self.user} subscribed to {self.forum}'


class ForumRead(models.Model):
    """Tracks which posts a user has read."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_reads'
    )
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE)
    thread = models.ForeignKey(ForumThread, on_delete=models.CASCADE)
    first_read = models.DateTimeField(auto_now_add=True)
    last_read = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'elening_forum_reads'
        unique_together = ('user', 'thread')
