from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from ckeditor.fields import RichTextField
from courses.models import Course, Lesson

class Quiz(models.Model):
    """测验模型"""
    title = models.CharField(max_length=200, verbose_name=_('Title'))
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='quizzes',
        verbose_name=_('Course')
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        related_name='quizzes',
        null=True,
        blank=True,
        verbose_name=_('Lesson')
    )
    description = models.TextField(blank=True, verbose_name=_('Description'))
    time_limit = models.PositiveIntegerField(
        help_text=_('Time limit in minutes (0 for no limit)'),
        default=0,
        verbose_name=_('Time Limit')
    )
    passing_score = models.PositiveIntegerField(
        default=70,
        help_text=_('Passing score in percentage'),
        verbose_name=_('Passing Score')
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
        return self.questions.all()
    
    def get_total_score(self):
        return sum(question.points for question in self.questions.all())

class Question(models.Model):
    """问题基础模型"""
    QUESTION_TYPES = (
        ('multiple_choice', _('Multiple Choice')),
        ('true_false', _('True/False')),
        ('fill_blank', _('Fill in the Blank')),
        ('essay', _('Essay')),
    )
    
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('Quiz')
    )
    question_text = RichTextField(verbose_name=_('Question Text'))
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPES,
        verbose_name=_('Question Type')
    )
    points = models.PositiveIntegerField(default=1, verbose_name=_('Points'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Order'))
    
    class Meta:
        verbose_name = _('Question')
        verbose_name_plural = _('Questions')
        ordering = ['order']
    
    def __str__(self):
        return self.question_text[:50]
    
    def get_choices(self):
        if self.question_type == 'multiple_choice':
            return self.choices.all()
        return None

class Choice(models.Model):
    """选择题选项模型"""
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='choices',
        verbose_name=_('Question')
    )
    choice_text = models.CharField(max_length=200, verbose_name=_('Choice Text'))
    is_correct = models.BooleanField(default=False, verbose_name=_('Is Correct'))
    
    class Meta:
        verbose_name = _('Choice')
        verbose_name_plural = _('Choices')
    
    def __str__(self):
        return self.choice_text

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

class QuizAttempt(models.Model):
    """测验尝试模型"""
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
    
    def __str__(self):
        return f"{self.student.username}'s attempt on {self.quiz.title}"
    
    def calculate_score(self):
        """计算测验得分"""
        total_points = self.quiz.get_total_score()
        if total_points == 0:
            return 0
        
        earned_points = sum(answer.earned_points for answer in self.answers.all())
        percentage = (earned_points / total_points) * 100
        self.score = percentage
        self.save()
        return percentage
    
    def passed(self):
        """检查是否通过测验"""
        return self.score >= self.quiz.passing_score

class Answer(models.Model):
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
        related_name='answers',
        verbose_name=_('Question')
    )
    selected_choices = models.ManyToManyField(
        Choice,
        blank=True,
        related_name='selected_in_answers',
        verbose_name=_('Selected Choices')
    )
    text_answer = models.TextField(blank=True, verbose_name=_('Text Answer'))
    earned_points = models.FloatField(default=0, verbose_name=_('Earned Points'))
    is_correct = models.BooleanField(default=False, verbose_name=_('Is Correct'))
    
    class Meta:
        verbose_name = _('Answer')
        verbose_name_plural = _('Answers')
        unique_together = ['attempt', 'question']
    
    def __str__(self):
        return f"Answer to {self.question}"
    
    def auto_grade(self):
        """自动评分功能"""
        question = self.question
        
        if question.question_type == 'multiple_choice':
            correct_choices = question.choices.filter(is_correct=True)
            selected_choices = self.selected_choices.all()
            
            # 检查选择是否完全匹配
            if set(correct_choices) == set(selected_choices):
                self.is_correct = True
                self.earned_points = question.points
            else:
                self.is_correct = False
                self.earned_points = 0
                
        elif question.question_type == 'true_false':
            # 假设只有一个正确选项
            correct_choice = question.choices.get(is_correct=True)
            if self.selected_choices.filter(id=correct_choice.id).exists():
                self.is_correct = True
                self.earned_points = question.points
            else:
                self.is_correct = False
                self.earned_points = 0
                
        elif question.question_type == 'fill_blank':
            # 简单的精确匹配，可以扩展为更复杂的匹配逻辑
            correct_answer = question.choices.get(is_correct=True).choice_text
            if self.text_answer.strip().lower() == correct_answer.strip().lower():
                self.is_correct = True
                self.earned_points = question.points
            else:
                self.is_correct = False
                self.earned_points = 0
                
        elif question.question_type == 'essay':
            # 论述题需要手动评分
            self.is_correct = False
            self.earned_points = 0
            
        self.save()
        return self.earned_points
