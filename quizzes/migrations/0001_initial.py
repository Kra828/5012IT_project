# Generated by Django 5.1.7 on 2025-03-18 14:30

import ckeditor.fields
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('courses', '0003_remove_course_category_delete_category'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_text', models.TextField(verbose_name='Question Text')),
                ('question_number', models.PositiveIntegerField(default=1, help_text='1 to 5', verbose_name='Question Number')),
            ],
            options={
                'verbose_name': 'Question',
                'verbose_name_plural': 'Questions',
                'ordering': ['question_number'],
            },
        ),
        migrations.CreateModel(
            name='Assignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Title')),
                ('description', ckeditor.fields.RichTextField(verbose_name='Description')),
                ('due_date', models.DateTimeField(verbose_name='Due Date')),
                ('total_points', models.PositiveIntegerField(default=100, verbose_name='Total Points')),
                ('is_published', models.BooleanField(default=False, verbose_name='Is Published')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='courses.course', verbose_name='Course')),
            ],
            options={
                'verbose_name': 'Assignment',
                'verbose_name_plural': 'Assignments',
                'ordering': ['-due_date'],
            },
        ),
        migrations.CreateModel(
            name='Choice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('choice_text', models.CharField(max_length=200, verbose_name='Choice Text')),
                ('is_correct', models.BooleanField(default=False, verbose_name='Is Correct')),
                ('choice_number', models.PositiveIntegerField(default=1, help_text='Option number (1-4)', verbose_name='Choice Number')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='choices', to='quizzes.question', verbose_name='Question')),
            ],
            options={
                'verbose_name': 'Choice',
                'verbose_name_plural': 'Choices',
                'ordering': ['choice_number'],
                'unique_together': {('question', 'choice_number')},
            },
        ),
        migrations.CreateModel(
            name='Quiz',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Title')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('time_limit', models.PositiveIntegerField(default=30, help_text='Time limit in minutes (0 for no limit)', verbose_name='Time Limit')),
                ('start_time', models.DateTimeField(blank=True, help_text='When the quiz becomes available to students', null=True, verbose_name='Start Time')),
                ('end_time', models.DateTimeField(blank=True, help_text='When the quiz is no longer available to students', null=True, verbose_name='End Time')),
                ('is_published', models.BooleanField(default=False, verbose_name='Is Published')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quizzes', to='courses.course', verbose_name='Course')),
            ],
            options={
                'verbose_name': 'Quiz',
                'verbose_name_plural': 'Quizzes',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='question',
            name='quiz',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='quizzes.quiz', verbose_name='Quiz'),
        ),
        migrations.CreateModel(
            name='QuizAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.FloatField(default=0, verbose_name='Score')),
                ('started_at', models.DateTimeField(auto_now_add=True, verbose_name='Started At')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='Completed At')),
                ('is_completed', models.BooleanField(default=False, verbose_name='Is Completed')),
                ('quiz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts', to='quizzes.quiz', verbose_name='Quiz')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quiz_attempts', to=settings.AUTH_USER_MODEL, verbose_name='Student')),
            ],
            options={
                'verbose_name': 'Quiz Attempt',
                'verbose_name_plural': 'Quiz Attempts',
                'unique_together': {('quiz', 'student')},
            },
        ),
        migrations.AlterUniqueTogether(
            name='question',
            unique_together={('quiz', 'question_number')},
        ),
        migrations.CreateModel(
            name='StudentAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attempt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='quizzes.quizattempt', verbose_name='Attempt')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_answers', to='quizzes.question', verbose_name='Question')),
                ('selected_choice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='selected_in_answers', to='quizzes.choice', verbose_name='Selected Choice')),
            ],
            options={
                'verbose_name': 'Student Answer',
                'verbose_name_plural': 'Student Answers',
                'unique_together': {('attempt', 'question')},
            },
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('submission_text', ckeditor.fields.RichTextField(blank=True, verbose_name='Submission Text')),
                ('submission_file', models.FileField(blank=True, null=True, upload_to='assignment_submissions/', verbose_name='Submission File')),
                ('submitted_at', models.DateTimeField(auto_now_add=True, verbose_name='Submitted At')),
                ('status', models.CharField(choices=[('submitted', 'Submitted'), ('graded', 'Graded'), ('returned', 'Returned for Revision')], default='submitted', max_length=20, verbose_name='Status')),
                ('score', models.PositiveIntegerField(blank=True, null=True, verbose_name='Score')),
                ('feedback', ckeditor.fields.RichTextField(blank=True, verbose_name='Feedback')),
                ('assignment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='quizzes.assignment', verbose_name='Assignment')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to=settings.AUTH_USER_MODEL, verbose_name='Student')),
            ],
            options={
                'verbose_name': 'Submission',
                'verbose_name_plural': 'Submissions',
                'unique_together': {('assignment', 'student')},
            },
        ),
    ]
