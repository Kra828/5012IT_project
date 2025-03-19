from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from ckeditor.fields import RichTextField
from courses.models import Course, Lesson
from django.utils import timezone

class Quiz(models.Model):
    """Quiz model - each quiz has a fixed set of 5 multiple-choice questions"""
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
        """Get questions for this quiz"""
        return self.questions.all()
    
    def is_available(self):
        """Check if quiz is available for students"""
        now = timezone.now()
        if not self.is_published:
            return False
        if self.start_time and now < self.start_time:
            return False
        if self.end_time and now > self.end_time:
            return False
        return True
    
    def delete(self, *args, **kwargs):
        """Override delete method for safe cascade deletion"""
        try:
            # Delete related attempts and answers
            for attempt in self.attempts.all():
                # Try to delete answers associated with this attempt
                attempt.answers.all().delete()
                attempt.delete()
            
            # Delete questions and choices
            for question in self.questions.all():
                question.choices.all().delete()
                question.delete()
            
            # Call parent delete method
            super().delete(*args, **kwargs)
        except Exception as e:
            # Log error and continue
            print(f"Error deleting quiz: {e}")
            
            # Force delete quiz
            super().delete(*args, **kwargs)

class Question(models.Model):
    """Question model - supports only multiple choice questions"""
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
        """Get choices for this question"""
        return self.choices.all()

class Choice(models.Model):
    """Choice model"""
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
    """Quiz attempt model - students can only attempt once"""
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
        """Calculate quiz score"""
        total_questions = self.quiz.questions.count()
        if total_questions == 0:
            return 0
        
        # Get the number of questions answered by the student
        student_answers = StudentAnswer.objects.filter(attempt=self)
        answered_questions_count = student_answers.count()
        
        # Get the number of correct answers
        correct_answers = student_answers.filter(selected_choice__is_correct=True).count()
        
        # Add debug information
        print(f"Debug - correct_answers: {correct_answers}, answered_questions: {answered_questions_count}, total_questions: {total_questions}")
        
        # Calculate the score based on number of correct answers divided by total questions
        # This ensures 2 correct answers out of 5 questions gives 40% not 20%
        score_percentage = (correct_answers / total_questions) * 100
            
        self.score = score_percentage
        self.save()
        return score_percentage

class StudentAnswer(models.Model):
    """Student answer model"""
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

# Keep the original Assignment and Submission models unchanged
class Assignment(models.Model):
    """Assignment model"""
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
    """Assignment submission model"""
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
