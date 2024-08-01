from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.Register.as_view()),
    path('login/', views.LoginAPIView.as_view()),
    path('change_password/', views.ChangePassword.as_view()),
    path('avatar/', views.Avatar.as_view()),
    path('name/', views.Name.as_view()),
    path('userinfo/', views.UserInfo.as_view()),
    path('phone/', views.SendSMSVerificationCode.as_view()),
]
