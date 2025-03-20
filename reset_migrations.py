#!/usr/bin/env python
"""
Reset migrations and database for a fresh start.
Run this script from the project root directory.
"""

import os
import shutil
import subprocess
from pathlib import Path

# List of Django apps in the project
APPS = [
    'accounts',
    'courses',
    'quizzes',
    'forum',
    'ai_assistant',
]

def run_command(command):
    """Run a shell command and print output"""
    print(f"Running: {command}")
    subprocess.run(command, shell=True, check=True)

def reset_migrations():
    """Delete all migration files and database"""
    # Remove database
    if os.path.exists('db.sqlite3'):
        os.remove('db.sqlite3')
        print("Removed database file: db.sqlite3")
    
    # Remove migration files
    for app in APPS:
        migrations_path = Path(app) / 'migrations'
        if migrations_path.exists():
            # Keep __init__.py file
            init_file = migrations_path / '__init__.py'
            has_init = init_file.exists()
            
            # Remove all migration files
            for file in migrations_path.glob('*.py'):
                if file.name != '__init__.py':
                    file.unlink()
                    print(f"Removed: {file}")
            
            # Remove __pycache__ directory
            pycache = migrations_path / '__pycache__'
            if pycache.exists():
                shutil.rmtree(pycache)
                print(f"Removed: {pycache}")
            
            # Recreate __init__.py if it existed
            if has_init and not init_file.exists():
                init_file.touch()
                print(f"Created: {init_file}")
    
    # Make migrations for each app
    for app in APPS:
        run_command(f"python manage.py makemigrations {app}")
    
    # Run migrations
    run_command("python manage.py migrate")
    
    # Create superuser
    print("\nCreating superuser...")
    run_command("python manage.py createsuperuser")

if __name__ == "__main__":
    # Ask for confirmation
    answer = input("This will reset all migrations and the database. Continue? (yes/no): ")
    if answer.lower() in ['yes', 'y']:
        reset_migrations()
        print("\nMigrations and database reset complete.")
    else:
        print("Operation cancelled.") 