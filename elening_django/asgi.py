import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elening_django.settings.development')
application = get_asgi_application()
