from django.urls import path
from . import views

app_name = "moderation"

urlpatterns = [
    path("", views.moderation_dashboard, name="dashboard"),
    path("courses/pending/", views.pending_courses, name="pending_courses"),
    path("instructor-applications/", views.instructor_applications, name="instructor_applications"),
    path("instructor-applications/<int:pk>/approve/", views.approve_instructor_application, name="approve_instructor_application"),
    path("instructor-applications/<int:pk>/reject/", views.reject_instructor_application, name="reject_instructor_application"),
    path("reports/", views.reports_list, name="reports"),
    path("reports/<int:pk>/", views.report_detail, name="report_detail"),
    path("disputes/", views.disputes_list, name="disputes"),
    path("enrollments/", views.EnrollmentListView.as_view(), name="enrollment_list"),
    path("users/<int:pk>/", views.user_moderate, name="user_moderate"),
    path("apply/instructor/", views.apply_instructor_role, name="apply_instructor_role"),
]

