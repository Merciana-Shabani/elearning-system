from django.urls import path
from . import views

app_name = 'assignments'

urlpatterns = [
    path('teaching/', views.InstructorAssignmentListView.as_view(), name='teaching_list'),
    path('course/<int:course_pk>/create/', views.AssignmentCreateView.as_view(), name='create'),
    path('course/<int:course_pk>/section/<int:section_pk>/create/', views.AssignmentCreateView.as_view(), name='create_in_section'),
    path('<int:pk>/', views.AssignmentDetailView.as_view(), name='detail'),
    path('<int:pk>/submit/', views.submit_assignment, name='submit'),
    path('<int:pk>/submissions/', views.SubmissionListView.as_view(), name='submissions'),
    path('submission/<int:submission_pk>/grade/', views.grade_submission, name='grade'),
]
