from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.InboxView.as_view(), name='inbox'),
    path('<int:pk>/', views.conversation_detail, name='conversation'),
    path('new/<int:user_pk>/', views.new_conversation, name='new_conversation'),
]
