# Elening LMS — Django Python

A full-featured Learning Management System converted from Moodle PHP to Django Python.

## Features

| Feature | Description |
|---------|-------------|
| **Users** | Custom user model with roles (Student, Teacher, Manager, Admin) |
| **Courses** | Course creation, categories, sections, modules |
| **Enrollment** | Open/manual/paid enrollment with key support |
| **Assignments** | File upload & online text submissions, grading |
| **Quizzes** | Multiple choice, true/false, short answer, essay — timed |
| **Forums** | Discussion threads, replies, subscriptions |
| **Grades** | Gradebook with categories, grade items, pass/fail |
| **Messaging** | Private conversations between users |
| **REST API** | Django REST Framework endpoints |
| **Admin** | Full Django admin panel |

## Tech Stack

- **Backend:** Django 4.2+, Python 3.10+
- **Database:** MySQL / MariaDB
- **Frontend:** Bootstrap 5, Bootstrap Icons
- **Auth:** django-allauth (email + social login)
- **Rich Text:** django-ckeditor
- **API:** Django REST Framework

## Quick Start

### 1. Create virtual environment

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your MySQL credentials and secret key
```

### 4. Create the MySQL database

```sql
CREATE DATABASE elening_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. Run migrations

```bash
python manage.py makemigrations users courses enrollment assignments quizzes forums grades messaging
python manage.py migrate
```

### 6. Create a superuser

```bash
python manage.py createsuperuser
```

### 7. Load static files and run

```bash
python manage.py collectstatic
python manage.py runserver
```

Open: http://localhost:8000

Admin panel: http://localhost:8000/admin/

---

## Project Structure

```
elening django/
├── manage.py
├── requirements.txt
├── .env.example
├── elening_django/
│   ├── settings/
│   │   ├── base.py          # Core settings
│   │   ├── development.py   # Dev overrides
│   │   └── production.py    # Production settings
│   ├── urls.py              # Root URL configuration
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── users/               # Custom user model, profiles
│   ├── courses/             # Courses, categories, sections, modules
│   ├── enrollment/          # Course enrollment management
│   ├── assignments/         # Assignments, submissions, grading
│   ├── quizzes/             # Quizzes, questions, attempts
│   ├── forums/              # Discussion forums
│   ├── grades/              # Gradebook
│   └── messaging/           # Private messages
├── templates/               # HTML templates (Bootstrap 5)
├── static/
│   ├── css/elening.css
│   └── js/elening.js
└── media/                   # User uploads
```

## Environment Variables (.env)

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | True/False |
| `DB_NAME` | MySQL database name |
| `DB_USER` | MySQL username |
| `DB_PASSWORD` | MySQL password |
| `DB_HOST` | MySQL host (default: localhost) |
| `DB_PORT` | MySQL port (default: 3306) |
| `EMAIL_HOST_USER` | SMTP email address |
| `EMAIL_HOST_PASSWORD` | SMTP password |

## Moodle → Django Mapping

| Moodle Table | Django Model |
|---|---|
| `mdl_user` | `users.User` |
| `mdl_course` | `courses.Course` |
| `mdl_course_categories` | `courses.CourseCategory` |
| `mdl_course_sections` | `courses.CourseSection` |
| `mdl_course_modules` | `courses.CourseModule` |
| `mdl_user_enrolments` | `enrollment.Enrollment` |
| `mdl_assign` | `assignments.Assignment` |
| `mdl_assign_submission` | `assignments.Submission` |
| `mdl_quiz` | `quizzes.Quiz` |
| `mdl_question` | `quizzes.Question` |
| `mdl_quiz_attempts` | `quizzes.QuizAttempt` |
| `mdl_forum` | `forums.Forum` |
| `mdl_forum_discussions` | `forums.ForumThread` |
| `mdl_forum_posts` | `forums.ForumPost` |
| `mdl_grade_items` | `grades.GradeItem` |
| `mdl_grade_grades` | `grades.Grade` |
| `mdl_messages` | `messaging.Message` |

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/courses/` | GET, POST | List / create courses |
| `/api/courses/<id>/` | GET, PUT, DELETE | Course detail |
| `/api/courses/categories/` | GET | List categories |
| `/api/users/` | GET | List users (admin) |
| `/api/users/<id>/` | GET, PUT | User detail |

## Production Deployment

1. Set `DEBUG=False` in `.env`
2. Set a strong `SECRET_KEY`
3. Configure `ALLOWED_HOSTS`
4. Use `elening_django.settings.production`
5. Run with `gunicorn elening_django.wsgi`
6. Set up nginx/Apache as reverse proxy
7. Use `python manage.py collectstatic`
