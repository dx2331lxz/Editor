from django.urls import path
from . import views

urlpatterns = [
    path('translate/', views.Translate.as_view()),
    path('summary/', views.Summary.as_view()),
    path('abstract/', views.Abstract.as_view()),
    path('continue/', views.Continue2Write.as_view()),
    path('wrong2right/', views.Wrong2Right.as_view()),
]
