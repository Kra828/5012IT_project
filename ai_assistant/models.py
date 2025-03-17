from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from courses.models import Course

class AIChat(models.Model):
    """AI Chat Session Model"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_chats',
        verbose_name=_('User')
    )
    title = models.CharField(max_length=200, verbose_name=_('Title'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    
    class Meta:
        verbose_name = _('AI Chat')
        verbose_name_plural = _('AI Chats')
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username}'s chat: {self.title}"
    
    def get_messages(self):
        """Get chat messages"""
        return self.messages.all().order_by('created_at')

class ChatMessage(models.Model):
    """Chat Message Model"""
    ROLE_CHOICES = (
        ('user', _('User')),
        ('assistant', _('Assistant')),
    )
    
    chat = models.ForeignKey(
        AIChat,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('Chat')
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        verbose_name=_('Role')
    )
    content = models.TextField(verbose_name=_('Content'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    
    class Meta:
        verbose_name = _('Chat Message')
        verbose_name_plural = _('Chat Messages')
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role} message in {self.chat.title}"

class LearningRecommendation(models.Model):
    """Learning Recommendation Model"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='learning_recommendations',
        verbose_name=_('User')
    )
    title = models.CharField(max_length=200, verbose_name=_('Title'))
    description = models.TextField(verbose_name=_('Description'))
    recommended_courses = models.ManyToManyField(
        Course,
        related_name='recommendations',
        blank=True,
        verbose_name=_('Recommended Courses')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    is_read = models.BooleanField(default=False, verbose_name=_('Is Read'))
    
    class Meta:
        verbose_name = _('Learning Recommendation')
        verbose_name_plural = _('Learning Recommendations')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Recommendation for {self.user.username}: {self.title}"
    
    def mark_as_read(self):
        """Mark as read"""
        self.is_read = True
        self.save()

class UserQuery(models.Model):
    """User Query Record Model"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_queries',
        verbose_name=_('User')
    )
    query = models.TextField(verbose_name=_('Query'))
    response = models.TextField(verbose_name=_('Response'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_queries',
        verbose_name=_('Related Course')
    )
    
    class Meta:
        verbose_name = _('User Query')
        verbose_name_plural = _('User Queries')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}'s query: {self.query[:50]}"

class LearningProgress(models.Model):
    """Learning Progress Tracking Model"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='learning_progress',
        verbose_name=_('User')
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='learning_progress',
        verbose_name=_('Course')
    )
    progress_percentage = models.FloatField(
        default=0,
        help_text=_('Progress percentage (0-100)'),
        verbose_name=_('Progress Percentage')
    )
    last_activity = models.DateTimeField(auto_now=True, verbose_name=_('Last Activity'))
    estimated_completion = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Estimated Completion Date')
    )
    
    class Meta:
        verbose_name = _('Learning Progress')
        verbose_name_plural = _('Learning Progress')
        unique_together = ['user', 'course']
    
    def __str__(self):
        return f"{self.user.username}'s progress in {self.course.title}: {self.progress_percentage}%"
    
    def update_progress(self, new_percentage):
        """Update progress percentage"""
        self.progress_percentage = new_percentage
        self.save()
        
        # If progress reaches 100%, trigger completion event
        if self.progress_percentage >= 100:
            self.mark_as_completed()
    
    def mark_as_completed(self):
        """Mark course as completed"""
        from courses.models import Enrollment
        enrollment = Enrollment.objects.get(student=self.user, course=self.course)
        enrollment.is_completed = True
        enrollment.save()

class OpenAISettings(models.Model):
    """OpenAI API Settings Model"""
    api_key_name = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name=_('API Key Name')
    )
    api_key = models.CharField(
        max_length=255, 
        verbose_name=_('API Key'),
        help_text=_('OpenAI API Key, please keep it secure')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Last Updated')
    )
    
    class Meta:
        verbose_name = _('OpenAI API Settings')
        verbose_name_plural = _('OpenAI API Settings')
        ordering = ['-last_updated']
    
    def __str__(self):
        return f"{self.api_key_name} ({'Active' if self.is_active else 'Inactive'})"
    
    def save(self, *args, **kwargs):
        """When saving, if this key is set active, set other keys to inactive"""
        if self.is_active:
            OpenAISettings.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)
    
    @classmethod
    def get_active_key(cls):
        """Get current active API key"""
        try:
            return cls.objects.filter(is_active=True).first().api_key
        except:
            return None
