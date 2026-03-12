from django.urls import path
from . import views

app_name = 'quizzes'

urlpatterns = [
    path('course/<int:course_pk>/create/', views.QuizCreateView.as_view(), name='create'),
    path('course/<int:course_pk>/section/<int:section_pk>/create/', views.QuizCreateView.as_view(), name='create_in_section'),
    path('', views.QuizListView.as_view(), name='list'),
    path('<int:pk>/', views.QuizDetailView.as_view(), name='detail'),
    path('<int:quiz_pk>/questions/add/', views.QuestionCreateView.as_view(), name='question_add'),
    path('question/<int:pk>/edit/', views.QuestionUpdateView.as_view(), name='question_edit'),
    path('question/<int:question_pk>/answers/add/', views.AnswerCreateView.as_view(), name='answer_add'),
    path('<int:pk>/start/', views.start_attempt, name='start'),
    path('attempt/<int:attempt_pk>/', views.take_attempt, name='attempt'),
    path('attempt/<int:attempt_pk>/result/', views.view_result, name='result'),
]
