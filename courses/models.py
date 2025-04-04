from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.conf import settings
from ckeditor.fields import RichTextField

class Course(models.Model):
    """Course model"""
    title = models.CharField(max_length=200, verbose_name=_('Title'))
    slug = models.SlugField(max_length=200, unique=True, verbose_name=_('Slug'))
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courses_taught',
        verbose_name=_('Instructor')
    )
    overview = RichTextField(verbose_name=_('Overview'))
    thumbnail = models.ImageField(
        upload_to='course_thumbnails/',
        blank=True,
        null=True,
        verbose_name=_('Thumbnail')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    is_published = models.BooleanField(default=False, verbose_name=_('Is Published'))
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='Enrollment',
        related_name='courses_enrolled',
        blank=True,
        verbose_name=_('Students')
    )
    
    class Meta:
        verbose_name = _('Course')
        verbose_name_plural = _('Courses')
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        """Generate unique slug when saving a new course"""
        if not self.slug:
            self.slug = slugify(self.title)
            original_slug = self.slug
            queryset = Course.objects.all()
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            
            # Ensure unique slug
            i = 1
            while queryset.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{i}"
                i += 1
        
        # Create forum board if needed
        from forum.models import DiscussionBoard
        super().save(*args, **kwargs)
        
        # Create discussion board for this course if it doesn't exist
        if not hasattr(self, 'discussion_board'):
            board = DiscussionBoard.objects.create(
                title=f"Discussion: {self.title}",
                description=f"Discussion board for {self.title} course",
                course=self
            )
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        """Get URL for course detail view"""
        return reverse('courses:course_detail', kwargs={'slug': self.slug})
    
    def delete(self, *args, **kwargs):
        """Delete course and related files"""
        # Delete media files
        if self.thumbnail:
            if os.path.isfile(self.thumbnail.path):
                os.remove(self.thumbnail.path)
        
        # Get all related lesson videos
        lessons = Lesson.objects.filter(chapter__course=self)
        for lesson in lessons:
            if lesson.video and os.path.isfile(lesson.video.path):
                os.remove(lesson.video.path)
        
        # Get all related course files
        course_files = self.files.all()
        for file in course_files:
            if file.file and os.path.isfile(file.file.path):
                os.remove(file.file.path)
        
        # Delete discussion board
        try:
            if hasattr(self, 'discussion_board'):
                self.discussion_board.delete()
        except:
            pass
        
        super().delete(*args, **kwargs)

class Chapter(models.Model):
    """Course chapter model"""
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='chapters',
        verbose_name=_('Course')
    )
    title = models.CharField(max_length=200, verbose_name=_('Title'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Order'))
    
    class Meta:
        verbose_name = _('Chapter')
        verbose_name_plural = _('Chapters')
        ordering = ['order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Lesson(models.Model):
    """Course video lesson model"""
    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name=_('Chapter')
    )
    title = models.CharField(max_length=200, verbose_name=_('Title'))
    video = models.FileField(upload_to='lesson_videos/', verbose_name=_('Video'))
    content = RichTextField(blank=True, verbose_name=_('Content'))
    duration = models.PositiveIntegerField(
        help_text=_('Duration in seconds'),
        verbose_name=_('Duration')
    )
    order = models.PositiveIntegerField(default=0, verbose_name=_('Order'))
    
    class Meta:
        verbose_name = _('Lesson')
        verbose_name_plural = _('Lessons')
        ordering = ['order']
    
    def __str__(self):
        return f"{self.chapter.title} - {self.title}"

class Enrollment(models.Model):
    """Student course enrollment model"""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name=_('Student')
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name=_('Course')
    )
    date_enrolled = models.DateTimeField(auto_now_add=True, verbose_name=_('Date Enrolled'))
    is_completed = models.BooleanField(default=False, verbose_name=_('Is Completed'))
    
    class Meta:
        verbose_name = _('Enrollment')
        verbose_name_plural = _('Enrollments')
        unique_together = ['student', 'course']
    
    def __str__(self):
        return f"{self.student.username} enrolled in {self.course.title}"

class LessonProgress(models.Model):
    """Student video watching progress model"""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lesson_progress',
        verbose_name=_('Student')
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='progress',
        verbose_name=_('Lesson')
    )
    current_position = models.PositiveIntegerField(
        default=0,
        help_text=_('Current position in seconds'),
        verbose_name=_('Current Position')
    )
    is_completed = models.BooleanField(default=False, verbose_name=_('Is Completed'))
    last_watched = models.DateTimeField(auto_now=True, verbose_name=_('Last Watched'))
    
    class Meta:
        verbose_name = _('Lesson Progress')
        verbose_name_plural = _('Lesson Progress')
        unique_together = ['student', 'lesson']
    
    def __str__(self):
        return f"{self.student.username}'s progress on {self.lesson.title}"

class CourseFile(models.Model):
    """Course file model for teachers to upload files for students to download"""
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='files',
        verbose_name=_('Course')
    )
    title = models.CharField(max_length=200, verbose_name=_('Title'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    file = models.FileField(upload_to='course_files/', verbose_name=_('File'))
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_files',
        verbose_name=_('Uploaded By')
    )
    upload_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Upload Date'))
    download_count = models.PositiveIntegerField(default=0, verbose_name=_('Download Count'))
    
    class Meta:
        verbose_name = _('Course File')
        verbose_name_plural = _('Course Files')
        ordering = ['-upload_date']
    
    def __str__(self):
        return self.title
    
    def increment_download_count(self):
        """Increment download count"""
        self.download_count += 1
        self.save()
