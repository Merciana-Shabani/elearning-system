@echo off
echo ============================================================
echo  Elening LMS - Django Setup Script
echo ============================================================
echo.

REM Create virtual environment
echo [1/6] Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM Install dependencies
echo [2/6] Installing Python dependencies...
pip install -r requirements.txt

REM Copy env file
echo [3/6] Setting up environment file...
if not exist .env (
    copy .env.example .env
    echo IMPORTANT: Edit .env and set your database credentials and SECRET_KEY!
    pause
)

REM Run migrations
echo [4/6] Running database migrations...
python manage.py makemigrations users courses enrollment assignments quizzes forums grades messaging
python manage.py migrate

REM Create superuser
echo [5/6] Creating superuser account...
python manage.py createsuperuser

REM Collect static files
echo [6/6] Collecting static files...
python manage.py collectstatic --noinput

echo.
echo ============================================================
echo  Setup complete! Run the server with:
echo    venv\Scripts\activate
echo    python manage.py runserver
echo  Then open: http://localhost:8000
echo ============================================================
pause
