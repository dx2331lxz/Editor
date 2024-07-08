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