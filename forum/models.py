from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from ckeditor.fields import RichTextField
from courses.models import Course

class DiscussionBoard(models.Model):
    """课程讨论板模型"""
    course = models.OneToOneField(
        Course,
        on_delete=models.CASCADE,
        related_name='discussion_board',
        verbose_name=_('Course')
    )
    description = models.TextField(blank=True, verbose_name=_('Description'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    
    class Meta:
        verbose_name = _('Discussion Board')
        verbose_name_plural = _('Discussion Boards')
    
    def __str__(self):
        return f"Discussion board for {self.course.title}"
    
    def get_latest_posts(self, count=5):
        """获取最新的帖子"""
        return self.posts.order_by('-created_at')[:count]
    
    def get_total_posts(self):
        """获取帖子总数"""
        return self.posts.count()

class Post(models.Model):
    """讨论帖模型"""
    board = models.ForeignKey(
        DiscussionBoard,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name=_('Discussion Board')
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='forum_posts',
        verbose_name=_('Author')
    )
    title = models.CharField(max_length=200, verbose_name=_('Title'))
    content = RichTextField(verbose_name=_('Content'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    is_pinned = models.BooleanField(default=False, verbose_name=_('Is Pinned'))
    is_announcement = models.BooleanField(default=False, verbose_name=_('Is Announcement'))
    views = models.PositiveIntegerField(default=0, verbose_name=_('Views'))
    
    class Meta:
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')
        ordering = ['-is_pinned', '-created_at']
    
    def __str__(self):
        return self.title
    
    def get_comment_count(self):
        """获取评论数量"""
        return self.comments.count()
    
    def increment_view(self):
        """增加浏览量"""
        self.views += 1
        self.save()

class Comment(models.Model):
    """评论模型"""
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('Post')
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='forum_comments',
        verbose_name=_('Author')
    )
    content = RichTextField(verbose_name=_('Content'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name=_('Parent Comment')
    )
    
    class Meta:
        verbose_name = _('Comment')
        verbose_name_plural = _('Comments')
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"
    
    def is_reply(self):
        """检查是否为回复"""
        return self.parent is not None
    
    def get_replies(self):
        """获取回复"""
        return self.replies.all()

class Like(models.Model):
    """点赞模型"""
    CONTENT_TYPES = (
        ('post', _('Post')),
        ('comment', _('Comment')),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='forum_likes',
        verbose_name=_('User')
    )
    content_type = models.CharField(
        max_length=10,
        choices=CONTENT_TYPES,
        verbose_name=_('Content Type')
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='likes',
        verbose_name=_('Post')
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='likes',
        verbose_name=_('Comment')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    
    class Meta:
        verbose_name = _('Like')
        verbose_name_plural = _('Likes')
        unique_together = [
            ['user', 'post'],
            ['user', 'comment'],
        ]
    
    def __str__(self):
        if self.content_type == 'post':
            return f"{self.user.username} liked post: {self.post.title}"
        else:
            return f"{self.user.username} liked a comment"

class Notification(models.Model):
    """通知模型"""
    NOTIFICATION_TYPES = (
        ('post', _('New Post')),
        ('comment', _('New Comment')),
        ('reply', _('New Reply')),
        ('like', _('New Like')),
    )
    
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='forum_notifications',
        verbose_name=_('Recipient')
    )
    notification_type = models.CharField(
        max_length=10,
        choices=NOTIFICATION_TYPES,
        verbose_name=_('Notification Type')
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Post')
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Comment')
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_notifications',
        verbose_name=_('Sender')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    is_read = models.BooleanField(default=False, verbose_name=_('Is Read'))
    
    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.recipient.username} - {self.get_notification_type_display()}"
    
    def mark_as_read(self):
        """标记为已读"""
        self.is_read = True
        self.save()
