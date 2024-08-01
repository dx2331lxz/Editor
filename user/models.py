from django.db import models
# 导入默认User
from django.contrib.auth.models import User
# Create your models here.
class Avatar(models.Model):
    """头像"""
    avatar = models.ImageField(upload_to='avatar', verbose_name='头像')
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='用户')

    class Meta:
        verbose_name = '头像'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.user.username

class UserInfo(models.Model):
    name = models.CharField(max_length=32, verbose_name='昵称')
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='用户')

# 登录ip记录
class LoginRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    ip = models.CharField(verbose_name='登录ip', max_length=32)
    login_time = models.DateTimeField(auto_now=True, verbose_name='登录时间')

    class Meta:
        verbose_name = '登录记录'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.user.username

# 用于手机验证码认证
class PhoneVerification(models.Model):
    phone_number = models.CharField(max_length=15, unique=True)
    verification_code = models.CharField(max_length=6)
    expiration_time = models.DateTimeField()