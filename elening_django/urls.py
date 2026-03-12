from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from apps.users import views as user_views

def home_view(request):
    if request.user.is_authenticated:
        if request.user.is_moderator:
            return redirect('moderation:dashboard')
        return redirect('users:user_dashboard', pk=request.user.pk)
    from django.shortcuts import render
    return render(request, "home.html")

def dashboard_redirect(request):
    """Send each user to their own dashboard URL."""
    if request.user.is_moderator:
        return redirect('moderation:dashboard')
    return redirect('users:user_dashboard', pk=request.user.pk)

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', home_view, name='home'),
    path('dashboard/', login_required(dashboard_redirect), name='dashboard'),

    # Signup step 1: choose user type
    path('accounts/set-signup-type/', user_views.set_signup_type, name='set_signup_type'),
    path('accounts/clear-signup-type/', user_views.clear_signup_type, name='clear_signup_type'),

    # Authentication (django-allauth)
    path('accounts/', include('allauth.urls')),

    # Apps
    path('users/', include('apps.users.urls', namespace='users')),
    path('courses/', include('apps.courses.urls', namespace='courses')),
    path('enrollment/', include('apps.enrollment.urls', namespace='enrollment')),
    path('assignments/', include('apps.assignments.urls', namespace='assignments')),
    path('quizzes/', include('apps.quizzes.urls', namespace='quizzes')),
    path('forums/', include('apps.forums.urls', namespace='forums')),
    path('grades/', include('apps.grades.urls', namespace='grades')),
    path('messages/', include('apps.messaging.urls', namespace='messaging')),
    path('conferences/', include('apps.conferences.urls', namespace='conferences')),
    path('moderation/', include('apps.moderation.urls', namespace='moderation')),

    # CKEditor
    path('ckeditor/', include('ckeditor_uploader.urls')),

    # REST API
    path('api/', include([
        path('courses/', include('apps.courses.api_urls')),
        path('users/', include('apps.users.api_urls')),
    ])),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
