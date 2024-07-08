from django.urls import path
from . import views

urlpatterns = [
    path('file/', views.File.as_view(), name='file'),
    path('photo/', views.Photo.as_view(), name='photo'),
    path('text/', views.Text.as_view(), name='text'),
    path('textall/', views.TextALL.as_view(), name='textall'),
]
