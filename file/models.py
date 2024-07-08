from django.db import models
from django.contrib.auth.models import User
# Create your models here.
#文件
class File(models.Model):
    file = models.FileField(upload_to='file', verbose_name='文件')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    time = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')

    class Meta:
        verbose_name = '文件'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.user

class Photo(models.Model):
    photo = models.ImageField(upload_to='photo', verbose_name='照片')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')

    class Meta:
        verbose_name = '照片'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.user.username
# 编辑内容
class Text(models.Model):
    content = models.TextField(verbose_name="文章内容", null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    # 自动修改时间

    time = models.DateTimeField(auto_now=True, verbose_name='修改时间', null=True, blank=True)

    name = models.CharField(verbose_name="文章名称", max_length=50)
    location_types = (
        (0, '云端'),
        (1, '本地'),
    )
    location_type = models.IntegerField(verbose_name="文章类型", default=0, choices=location_types)
    location = models.CharField(verbose_name="文章位置", max_length=50, blank=True, null=True)
    size = models.IntegerField(verbose_name="文章大小")

