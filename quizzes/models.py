from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from ckeditor.fields import RichTextField
from courses.models import Course, Lesson
from django.utils import timezone

class Quiz(models.Model):
    """测验模型 - 每个测验有固定的5个多选题"""
    title = models.CharField(max_length=200, verbose_name=_('Title'))
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='quizzes',
        verbose_name=_('Course')
    )
    description = models.TextField(blank=True, verbose_name=_('Description'))
    time_limit = models.PositiveIntegerField(
        help_text=_('Time limit in minutes (0 for no limit)'),
        default=30,
        verbose_name=_('Time Limit')
    )
    start_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Start Time'),
        help_text=_('When the quiz becomes available to students')
    )
    end_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('End Time'),
        help_text=_('When the quiz is no longer available to students')
    )
    is_published = models.BooleanField(default=False, verbose_name=_('Is Published'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    
    class Meta:
        verbose_name = _('Quiz')
        verbose_name_plural = _('Quizzes')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_questions(self):
        """获取测验的问题"""
        return self.questions.all().order_by('question_number')
    
    def is_available(self):
        """检查测验是否可用"""
        now = timezone.now()
        if not self.is_published:
            return False
        if self.start_time and now < self.start_time:
            return False
        if self.end_time and now > self.end_time:
            return False
        return True
    
    def delete(self, *args, **kwargs):
        """重写删除方法，安全处理级联删除"""
        try:
            # 删除相关的尝试和答案
            for attempt in self.attempts.all():
                try:
                    # 尝试删除与此尝试相关的答案
                    from django.db import connection
                    with connection.cursor() as cursor:
                        try:
                            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quizzes_studentanswer'")
                            if cursor.fetchone():
                                cursor.execute(f"DELETE FROM quizzes_studentanswer WHERE attempt_id = {attempt.id}")
                        except Exception:
                            pass
                    attempt.delete()
                except Exception:
                    pass
            
            # 删除问题和选项
            for question in self.questions.all():
                try:
                    question.delete()
                except Exception:
                    pass
            
            # 调用父类删除方法
            super().delete(*args, **kwargs)
        except Exception as e:
            # 记录错误并继续
            from django.db import connection
            connection.set_rollback(True)
            # 强制删除测验
            with connection.cursor() as cursor:
                cursor.execute(f"DELETE FROM quizzes_quiz WHERE id = {self.id}")

class Question(models.Model):
    """问题模型 - 仅支持多选题"""
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('Quiz')
    )
    question_text = models.TextField(verbose_name=_('Question Text'))
    question_number = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Question Number'),
        help_text=_('1 to 5')
    )
    
    class Meta:
        verbose_name = _('Question')
        verbose_name_plural = _('Questions')
        ordering = ['question_number']
        unique_together = ['quiz', 'question_number']
    
    def __str__(self):
        return f"{self.quiz.title} - Q{self.question_number}: {self.question_text[:30]}"
    
    def get_choices(self):
        """获取问题的选项"""
        return self.choices.all()

class Choice(models.Model):
    """选项模型"""
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='choices',
        verbose_name=_('Question')
    )
    choice_text = models.CharField(max_length=200, verbose_name=_('Choice Text'))
    is_correct = models.BooleanField(default=False, verbose_name=_('Is Correct'))
    choice_number = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Choice Number'),
        help_text=_('Option number (1-4)')
    )
    
    class Meta:
        verbose_name = _('Choice')
        verbose_name_plural = _('Choices')
        ordering = ['choice_number']
        unique_together = ['question', 'choice_number']
    
    def __str__(self):
        return f"Option {self.choice_number}: {self.choice_text}"

class QuizAttempt(models.Model):
    """测验尝试模型 - 学生只能尝试一次"""
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name=_('Quiz')
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
        verbose_name=_('Student')
    )
    score = models.FloatField(default=0, verbose_name=_('Score'))
    started_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Started At'))
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Completed At'))
    is_completed = models.BooleanField(default=False, verbose_name=_('Is Completed'))
    
    class Meta:
        verbose_name = _('Quiz Attempt')
        verbose_name_plural = _('Quiz Attempts')
        unique_together = ['quiz', 'student']
    
    def __str__(self):
        return f"{self.student.username}'s attempt on {self.quiz.title}"
    
    def calculate_score(self):
        """计算测验得分"""
        total_questions = self.quiz.questions.count()
        if total_questions == 0:
            return 0
        
        correct_answers = StudentAnswer.objects.filter(
            attempt=self,
            selected_choice__is_correct=True
        ).count()
        
        score_percentage = (correct_answers / total_questions) * 100
        self.score = score_percentage
        self.save()
        return score_percentage

class StudentAnswer(models.Model):
    """学生答案模型"""
    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name=_('Attempt')
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='student_answers',
        verbose_name=_('Question')
    )
    selected_choice = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        related_name='selected_in_answers',
        verbose_name=_('Selected Choice')
    )
    
    class Meta:
        verbose_name = _('Student Answer')
        verbose_name_plural = _('Student Answers')
        unique_together = ['attempt', 'question']
    
    def __str__(self):
        return f"Answer for {self.question}"

# 保留原有的Assignment和Submission模型不变
class Assignment(models.Model):
    """作业模型"""
    title = models.CharField(max_length=200, verbose_name=_('Title'))
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name=_('Course')
    )
    description = RichTextField(verbose_name=_('Description'))
    due_date = models.DateTimeField(verbose_name=_('Due Date'))
    total_points = models.PositiveIntegerField(default=100, verbose_name=_('Total Points'))
    is_published = models.BooleanField(default=False, verbose_name=_('Is Published'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    
    class Meta:
        verbose_name = _('Assignment')
        verbose_name_plural = _('Assignments')
        ordering = ['-due_date']
    
    def __str__(self):
        return self.title

class Submission(models.Model):
    """作业提交模型"""
    STATUS_CHOICES = (
        ('submitted', _('Submitted')),
        ('graded', _('Graded')),
        ('returned', _('Returned for Revision')),
    )
    
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name=_('Assignment')
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name=_('Student')
    )
    submission_text = RichTextField(blank=True, verbose_name=_('Submission Text'))
    submission_file = models.FileField(
        upload_to='assignment_submissions/',
        blank=True,
        null=True,
        verbose_name=_('Submission File')
    )
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Submitted At'))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='submitted',
        verbose_name=_('Status')
    )
    score = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('Score'))
    feedback = RichTextField(blank=True, verbose_name=_('Feedback'))
    
    class Meta:
        verbose_name = _('Submission')
        verbose_name_plural = _('Submissions')
        unique_together = ['assignment', 'student']
    
    def __str__(self):
        return f"{self.student.username}'s submission for {self.assignment.title}"
    
    def is_late(self):
        return self.submitted_at > self.assignment.due_date
