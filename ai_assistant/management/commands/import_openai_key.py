from django.core.management.base import BaseCommand
from django.conf import settings
from ai_assistant.models import OpenAISettings


class Command(BaseCommand):
    help = 'Import OpenAI API key from settings to database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if an active key already exists',
        )

    def handle(self, *args, **options):
        # Get API key from settings
        api_key = settings.OPENAI_API_KEY
        
        if not api_key:
            self.stdout.write(self.style.ERROR('Error: No OPENAI_API_KEY found in settings'))
            return
        
        # Check if there is already an active API key
        existing_active = OpenAISettings.objects.filter(is_active=True).first()
        
        if existing_active and not options['force']:
            self.stdout.write(
                self.style.WARNING(f"An active API key already exists: {existing_active.api_key_name}")
            )
            self.stdout.write(
                self.style.WARNING("Use --force to replace the existing active API key")
            )
            return
        
        # Create new API key settings
        api_settings = OpenAISettings(
            api_key_name="API key imported from settings",
            api_key=api_key,
            is_active=True
        )
        api_settings.save()
        
        self.stdout.write(
            self.style.SUCCESS(f"API key successfully imported to database with name: {api_settings.api_key_name}")
        )
        self.stdout.write(
            self.style.SUCCESS("You can now manage this API key through the admin interface")
        ) 