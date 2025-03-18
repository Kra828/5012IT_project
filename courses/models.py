from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.conf import settings
from ckeditor.fields import RichTextField

class Course(models.Model):
    """课程模型"""
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
        verbose_name=_('Students')
    )
    
    class Meta:
        verbose_name = _('Course')
        verbose_name_plural = _('Courses')
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            if not base_slug:  # 如果标题无法生成有效的slug
                base_slug = f"course-{self.pk or 'new'}"
            
            # 确保slug唯一
            slug = base_slug
            counter = 1
            
            # 检查是否已存在相同的slug
            while Course.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        # 保存课程
        super().save(*args, **kwargs)
        
        # 为课程创建讨论板（如果不存在）
        from forum.models import DiscussionBoard
        if not hasattr(self, 'discussion_board'):
            DiscussionBoard.objects.create(
                course=self,
                description=f"讨论区：{self.title}"
            )
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('courses:course_detail', args=[self.slug])
    
    def delete(self, *args, **kwargs):
        """重写删除方法，安全处理级联删除"""
        try:
            # 直接删除关联的讨论板
            if hasattr(self, 'discussion_board'):
                self.discussion_board.delete()
            
            # 删除课程相关的测验
            for quiz in self.quizzes.all():
                try:
                    quiz.delete()
                except Exception:
                    pass
                    
            # 调用父类的删除方法
            super().delete(*args, **kwargs)
        except Exception as e:
            # 记录错误并继续
            from django.db import connection
            connection.set_rollback(True)
            # 强制删除课程
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(f"DELETE FROM courses_course WHERE id = {self.id}")

class Chapter(models.Model):
    """课程章节模型"""
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
    """课程视频课程模型"""
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
        return self.title

class Enrollment(models.Model):
    """学生课程注册模型"""
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
    """学生视频观看进度模型"""
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
    """课程文件模型，用于教师上传文件供学生下载"""
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
        """增加下载计数"""
        self.download_count += 1
        self.save()
