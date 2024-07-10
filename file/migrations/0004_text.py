# Generated by Django 4.1.4 on 2024-07-02 19:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('file', '0003_photo'),
    ]

    operations = [
        migrations.CreateModel(
            name='Text',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(blank=True, null=True, verbose_name='文章内容')),
                ('time', models.DateTimeField(auto_now_add=True, verbose_name='修改时间')),
                ('name', models.CharField(max_length=50, verbose_name='文章名称')),
                ('location_type', models.IntegerField(choices=[(0, '云端'), (1, '本地')], default=0, verbose_name='文章类型')),
                ('location', models.CharField(blank=True, max_length=50, null=True, verbose_name='文章位置')),
                ('size', models.IntegerField(verbose_name='文章大小')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
        ),
    ]