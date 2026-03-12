from django.urls import path
from . import api_views

urlpatterns = [
    path('', api_views.UserListAPIView.as_view(), name='api-user-list'),
    path('<int:pk>/', api_views.UserDetailAPIView.as_view(), name='api-user-detail'),
]
