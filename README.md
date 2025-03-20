# Smart Interactive Learning Platform

An advanced online learning platform built with Django, designed to facilitate teaching and learning through an interactive web application.

## Features

- **User Management**: Different user roles (students, teachers, admin) with appropriate permissions
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

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/Kra828/5012IT_project.git
   cd 5012IT_project
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Apply migrations:
   ```
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

## Environment Variables

Create a `.env` file in the project root with the following variables:

```
SECRET_KEY=your_secret_key
DEBUG=True
OPENAI_API_KEY=your_openai_api_key
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
