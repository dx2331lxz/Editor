from django.urls import path
from . import views

urlpatterns = [
    path('translate/', views.Translate.as_view()),
    path('summary/', views.Summary.as_view()),
    path('abstract/', views.Abstract.as_view()),
    path('continue/', views.Continue2Write.as_view()),
    path('wrong2right/', views.Wrong2Right.as_view()),
    path('polish/', views.Polish.as_view()),
    path('ocr/', views.OCR.as_view()),
    path('objectdetection/', views.ObjectDetection.as_view()),
    path('mysystem/', views.MysystemAPIView.as_view()),
    path('speech/', views.SpeechAPIView.as_view()),
    path('table/', views.TableAPIView.as_view()),
    path('codecompletion1/', views.CodeCompletion_1_APIView.as_view()),
]
