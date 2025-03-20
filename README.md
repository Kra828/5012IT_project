# Smart Interactive Learning Platform

An advanced online learning platform built with Django, designed to facilitate teaching and learning through an interactive web application.

## Features

- **User Management**: Different user roles (students, teachers, admin) with appropriate permissions
  - New users automatically registered as students
  - Only administrators can promote users to teacher role
- **Course Management**: Create, update, and manage courses with video lessons and chapter structure
- **Student Progress Tracking**: Track student progress through courses and lessons
- **Quiz System**: Create and take quizzes with various question types
- **Discussion Forum**: Course-specific discussion boards for student-teacher interaction
- **File Management**: Upload and download course materials
- **AI Assistant**: Integrated AI assistant powered by OpenAI API for enhanced learning experience

## Technology Stack

- **Backend**: Django 5.1.7
- **Frontend**: Bootstrap, JavaScript
- **Database**: SQLite (development), PostgreSQL (production ready)
- **Media Storage**: Local file system with option for cloud storage
- **Authentication**: Custom user model + Django allauth
- **Rich Text Editing**: CKEditor
- **AI Integration**: OpenAI API

## Setup Instructions

### First-time Setup

1. Clone this repository
2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Set up the database:
   ```
   python manage.py makemigrations accounts courses quizzes forum ai_assistant
   python manage.py migrate
   ```
5. Create a superuser:
   ```
   python manage.py createsuperuser
   ```
6. Run the development server:
   ```
   python manage.py runserver
   ```

### Troubleshooting Migration Issues

If you encounter migration issues after pulling new code:

#### Option 1: Reset migrations using our script
1. Make sure you have activated your virtual environment
2. Run the migration reset script:
   ```
   python reset_migrations.py
   ```
   This script will:
   - Delete the database file
   - Remove all migration files
   - Create new migrations
   - Apply migrations
   - Prompt you to create a new superuser

#### Option 2: Manual reset
1. Delete the database file:
   ```
   rm db.sqlite3
   ```
2. Delete migration files in each app folder:
   ```
   find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
   find . -path "*/migrations/*.pyc" -delete
   ```
3. Create new migrations:
   ```
   python manage.py makemigrations accounts courses quizzes forum ai_assistant
   ```
4. Apply migrations:
   ```
   python manage.py migrate
   ```
5. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

## Common Issues

### Database Issues
- If you see errors about tables not existing or columns not matching, try resetting migrations using the instructions above

## Environment Variables
Create a `.env` file in the project root with the following variables:

```
# Django settings
SECRET_KEY=your-secret-key
DEBUG=True

# OpenAI API settings (if using AI features)
OPENAI_API_KEY=your-openai-api-key
```

## Project Structure

- **accounts**: Custom user model and authentication
- **courses**: Course management and lesson progress tracking
- **quizzes**: Quiz creation and assessment
- **forum**: Discussion board functionality
- **ai_assistant**: AI-powered learning assistant

## License

This project is open-source, available under the MIT License.

## Contact

For any questions or suggestions, please contact [2960845D@student.gla.ac.uk](mailto:2960845D@student.gla.ac.uk).