from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('', views.UserListView.as_view(), name='list'),
    path('<int:pk>/dashboard/', views.user_dashboard, name='user_dashboard'),
    path('<int:pk>/', views.UserProfileView.as_view(), name='profile'),
    path('edit/', views.edit_profile, name='edit_profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
]
