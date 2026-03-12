from django.urls import path
from . import views

app_name = 'enrollment'

urlpatterns = [
    path('my-courses/', views.MyCoursesView.as_view(), name='my_courses'),
    path('assignments-done/', views.AssignmentsDoneView.as_view(), name='assignments_done'),
    path('quizzes-done/', views.QuizzesDoneView.as_view(), name='quizzes_done'),
    path('teaching/enrollments/', views.InstructorEnrollmentsView.as_view(), name='instructor_enrollments'),
    path('study-list/', views.StudyListView.as_view(), name='study_list'),
    path('study-list/add/<int:course_pk>/', views.study_list_add, name='study_list_add'),
    path('study-list/remove/<int:course_pk>/', views.study_list_remove, name='study_list_remove'),
    path('enroll/<int:course_pk>/', views.enroll_course, name='enroll'),
    path('unenroll/<int:course_pk>/', views.unenroll_course, name='unenroll'),
]
