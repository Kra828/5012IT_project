# Generated by Django 5.1.7 on 2025-03-18 15:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quizzes', '0002_auto_20250318_1451'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='question_number',
            field=models.PositiveIntegerField(default=1, help_text='1 to 5', verbose_name='Question Number'),
        ),
        migrations.AlterUniqueTogether(
            name='question',
            unique_together={('quiz', 'question_number')},
        ),
    ]
