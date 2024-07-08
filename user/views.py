from django.shortcuts import render, HttpResponse
from . import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, pagination  # 状态和分页
from rest_framework.parsers import MultiPartParser  # 文件上传`MultiPartParser`解析器
import json
import os
# 导入默认User
from django.contrib.auth.models import User
# jwt
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication, JWTTokenUserAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

# 注册账号
class Register(APIView):
    permission_classes = [AllowAny]
    # 检验密码强度
    def check_password(self, password):
        score = 0
        """
        一、密码长度:
            5 分: 小于等于 4 个字符
            10 分: 5 到 7 字符
            25 分: 大于等于 8 个字符
            
            二、字母:
            
            0 分: 没有字母
            10 分: 全都是小（大）写字母20 分: 大小写混合字母
            
            三、数字:
            
            0分: 没有数字
            10分: 1 个数字
            20分: 大于等于 3个数字
            
            四、符号:
            
            0分: 没有符号
            10分: 1个符号
            25分: 大于1个符号
            
            五、奖励:
            
            2分: 字母和数字
            3分: 字母、数字和符号
            5分: 大小写字母、数字和符号
        :param password: 密码
        :return: 分数
        """
        # 长度
        if len(password) <= 4:
            score += 5
        elif 5 <= len(password) <= 7:
            score += 10
        else:
            score += 25

        # 字母
        if password.isalpha():
            score += 0
        elif password.islower() or password.isupper():
            score += 10
        else:
            score += 20

        # 数字
        if password.isdigit():
            score += 0
        elif len([i for i in password if i.isdigit()]) >= 3:
            score += 20
        else:
            score += 10

        # 符号
        if len([i for i in password if i.isalnum()]) == 0:
            score += 0
        elif len([i for i in password if not i.isalnum()]) == 1:
            score += 10
        else:
            score += 25

        # 奖励
        if len([i for i in password if i.isalpha()]) > 0 and len([i for i in password if i.isdigit()]) > 0:
            score += 2
        if len([i for i in password if i.isalpha()]) > 0 and len([i for i in password if i.isdigit()]) > 0 and len(
                [i for i in password if not i.isalnum()]) > 0:
            score += 3
        if len([i for i in password if i.islower()]) > 0 and len([i for i in password if i.isupper()]) > 0 and len(
                [i for i in password if i.isdigit()]) > 0 and len([i for i in password if not i.isalnum()]) > 0:
            score += 5

        return score

    def post(self, request):
        data = request.data
        username = data.get('username')
        password = data.get('password')
        re_password = data.get('re_password')
        if not username or not password:
            return Response({'msg': '请输入用户名和密码'}, status=status.HTTP_400_BAD_REQUEST)
        if password != re_password:
            return Response({'msg': '两次密码不一致'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return Response({'msg': '用户名已存在'}, status=status.HTTP_400_BAD_REQUEST)
        score = self.check_password(password)
        if score < 50:
            return Response({'msg': '密码强度不够'}, status=status.HTTP_400_BAD_REQUEST)

        User.objects.create_user(username=username, password=password)
        return Response({'msg': '注册成功'}, status=status.HTTP_201_CREATED)
# 修改密码
class ChangePassword(APIView):

    def post(self, request):
        user_id = request.user.id
        user = User.objects.get(id=user_id)
        data = request.data
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        re_new_password = data.get('re_new_password')
        if not old_password or not new_password:
            return Response({'msg': '请输入旧密码和新密码'}, status=status.HTTP_400_BAD_REQUEST)
        if new_password != re_new_password:
            return Response({'msg': '两次密码不一致'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(old_password):
            return Response({'msg': '旧密码错误'}, status=status.HTTP_400_BAD_REQUEST)
        score = Register().check_password(new_password)
        if score < 50:
            return Response({'msg': '密码强度不够'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({'msg': '修改密码成功'}, status=status.HTTP_200_OK)

# 上传头像
class Avatar(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        user_id = request.user.id
        user = User.objects.get(id=user_id)
        avatar = request.data.get('avatar')
        if not avatar:
            return Response({'msg': '请选择头像'}, status=status.HTTP_400_BAD_REQUEST)
        # 限制上传文件大小
        if avatar.size > 1024 * 1024 * 2:
            return Response({'msg': '图片大小不能超过2M'}, status=status.HTTP_400_BAD_REQUEST)
        # 限制上传文件类型
        ext = os.path.splitext(avatar.name)[1]
        if ext not in ['.jpg', '.jpeg', '.png', '.gif']:
            return Response({'msg': '图片格式不正确'}, status=status.HTTP_400_BAD_REQUEST)
        models.Avatar.objects.update_or_create(user=user, defaults={'avatar': avatar})

        return Response({'msg': '上传头像成功'}, status=status.HTTP_201_CREATED)

    def get(self, request):
        user_id = request.user.id
        user = User.objects.get(id=user_id)
        avatar = models.Avatar.objects.filter(user=user).first()
        if not avatar:
            return Response({'msg': '未上传头像'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'url': avatar.avatar.url}, status=status.HTTP_200_OK)

#  修改昵称
class Name(APIView):

    def post(self, request):
        user_id = request.user.id
        user = User.objects.get(id=user_id)
        data = request.data
        name = data.get('name')
        if not name:
            return Response({'msg': '请输入昵称'}, status=status.HTTP_400_BAD_REQUEST)
        models.UserInfo.objects.update_or_create(user=user, defaults={'name': name})
        return Response({'msg': '修改昵称成功'}, status=status.HTTP_200_OK)

#  获取昵称
    def get(self, request):
        user_id = request.user.id
        user = User.objects.get(id=user_id)
        name = models.UserInfo.objects.filter(user=user).first()
        if not name:
            return Response({'msg': '未设置昵称'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'name': name.name}, status=status.HTTP_200_OK)


# 获取全部用户信息
class UserInfo(APIView):
    def get(self, request):
        user_id = request.user.id
        user = User.objects.get(id=user_id)
        name = models.UserInfo.objects.filter(user=user).first()
        avatar = models.Avatar.objects.filter(user=user).first()
        res = {
            'name': name.name if name else '',
            'avatar': avatar.avatar.url if avatar else ''
        }
        return Response(res, status=status.HTTP_200_OK)