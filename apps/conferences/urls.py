from django.urls import path
from . import views

app_name = 'conferences'

urlpatterns = [
    path('', views.RoomListView.as_view(), name='list'),
    path('create/', views.create_room, name='create'),
    path('<uuid:slug>/', views.join_room, name='room'),
    path('<uuid:slug>/end/', views.end_room, name='end'),
    path('<uuid:slug>/delete/', views.delete_room, name='delete'),
]
