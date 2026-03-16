# elening_django/settings.py

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-your-secret-key-here-change-this!'  # Badilisha hii kwa strong key (tumia python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

DEBUG = True

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "[::1]",
]

# If you access the dev server via a different hostname (e.g. LAN IP, tunnel),
# add it to both ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS.
CSRF_TRUSTED_ORIGINS = [
    "http://localhost",
    "http://127.0.0.1",
    "http://[::1]",
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Ongeza apps zako hapa, k.m.
    # 'apps.home',
    # 'apps.yourapp',
    # 'ckeditor',  # kama unatumia
    # 'allauth', 'allauth.account', n.k.
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'elening_django.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'elening_django.wsgi.application'

# Database (hii ndiyo iliyokuletea error ya awali)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'elening_db',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

LANGUAGE_CODE = 'en-us'  # au 'sw' kwa Kiswahili
TIME_ZONE = 'Africa/Dar_es_Salaam'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login itumie username + password (sio email)
ACCOUNT_LOGIN_METHODS = {'username'}

# Signup form fields: username required, password required, confirm password required
# Hakuna email field hapa (email itakuwa optional au hidden)
ACCOUNT_SIGNUP_FIELDS = [
    'username*',       # * inamaanisha required
    'password1*',
    'password2*',
]

# Optional: Email si required kabisa wakati wa signup
ACCOUNT_EMAIL_REQUIRED = False          # (hii deprecated lakini bado inafaa kama backup)
ACCOUNT_UNIQUE_EMAIL = False            # kama hutaki email iwe unique

# Optional: Kama hutaki verification ya email kabisa
ACCOUNT_EMAIL_VERIFICATION = 'none'

# Hakikisha username inafanya kazi vizuri (default ni hii)
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'  # kama una default User model