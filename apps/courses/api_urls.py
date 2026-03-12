from django.urls import path
from . import api_views

urlpatterns = [
    path('', api_views.CourseListAPIView.as_view(), name='api-course-list'),
    path('<int:pk>/', api_views.CourseDetailAPIView.as_view(), name='api-course-detail'),
    path('categories/', api_views.CourseCategoryListAPIView.as_view(), name='api-category-list'),
]
