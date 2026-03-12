from django.urls import path
from . import views

app_name = 'forums'

urlpatterns = [
    path('<int:pk>/', views.ForumDetailView.as_view(), name='detail'),
    path('<int:forum_pk>/create/', views.create_thread, name='create_thread'),
    path('thread/<int:pk>/', views.ThreadDetailView.as_view(), name='thread'),
    path('thread/<int:thread_pk>/reply/', views.reply_to_thread, name='reply'),
]
