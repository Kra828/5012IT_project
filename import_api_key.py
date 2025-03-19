#!/usr/bin/env python
"""
Import OpenAI API key from .env file to the database
"""
import os
import django
import sys
from pathlib import Path
from dotenv import load_dotenv

# Setup Django environment
sys.path.append(str(Path(__file__).resolve().parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elearning.settings')
django.setup()

# Import models
from ai_assistant.models import OpenAISettings

def import_api_key():
    """Import API key from .env file to the database"""
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("Error: No OPENAI_API_KEY found in .env file")
        return
    
    # Check if there is already an active API key
    existing_active = OpenAISettings.objects.filter(is_active=True).first()
    
    if existing_active:
        print(f"An active API key already exists: {existing_active.api_key_name}")
        choice = input("Do you want to replace the existing active API key? (y/n): ")
        if choice.lower() != 'y':
            print("Operation canceled")
            return
    
    # Create new API key settings
    api_settings = OpenAISettings(
        api_key_name="API key imported from environment variables",
        api_key=api_key,
        is_active=True
    )
    api_settings.save()
    
    print(f"API key successfully imported to database with name: {api_settings.api_key_name}")
    print("You can now manage this API key through the admin interface")

if __name__ == "__main__":
    import_api_key() 