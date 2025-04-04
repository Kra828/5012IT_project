# Generated by Django 5.1.7 on 2025-03-17 19:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_assistant', '0002_openaisettings'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='openaisettings',
            options={'ordering': ['-last_updated'], 'verbose_name': 'OpenAI API Settings', 'verbose_name_plural': 'OpenAI API Settings'},
        ),
        migrations.AlterField(
            model_name='openaisettings',
            name='api_key',
            field=models.CharField(help_text='OpenAI API Key, please keep it secure', max_length=255, verbose_name='API Key'),
        ),
        migrations.AlterField(
            model_name='openaisettings',
            name='api_key_name',
            field=models.CharField(max_length=100, unique=True, verbose_name='API Key Name'),
        ),
        migrations.AlterField(
            model_name='openaisettings',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Is Active'),
        ),
        migrations.AlterField(
            model_name='openaisettings',
            name='last_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Last Updated'),
        ),
    ]
