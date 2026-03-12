from django.urls import path
from . import views

app_name = 'grades'

urlpatterns = [
    path('course/<int:course_pk>/', views.gradebook, name='gradebook'),
]
