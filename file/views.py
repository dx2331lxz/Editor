from django.shortcuts import render, HttpResponse
from . import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, pagination  # 状态和分页
from rest_framework.parsers import MultiPartParser, JSONParser  # 文件上传`MultiPartParser`解析器

import json
import os
from Editor import settings
from django.core.files.storage import default_storage


# 上传文件

class File(APIView):
    parser_classes = [MultiPartParser, JSONParser]

    def post(self, request):
        user_id = request.user.id
        user = models.User.objects.get(id=user_id)
        content = request.data.get('content')
        if not content:
            return Response({'msg': '请输入内容'}, status=status.HTTP_400_BAD_REQUEST)
        file_name = request.data.get('file_name')
        if not file_name:
            return Response({'msg': '请输入文件名'}, status=status.HTTP_400_BAD_REQUEST)
        while default_storage.exists(os.path.join(settings.MEDIA_ROOT, 'file', file_name)):
            file_name = f'{os.path.splitext(file_name)[0]}_copy{os.path.splitext(file_name)[1]}'
        file_name = file_name + '.txt'
        file_path = os.path.join(settings.MEDIA_ROOT, 'file', file_name)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        file_name = os.path.join('file', file_name)
        print(file_name)
        obj = models.File.objects.create(file=file_name, user=user)
        return Response({'msg': '上传成功', 'file_path': obj.file.url}, status=status.HTTP_200_OK)

        # file = request.data.get('file')
        #
        # if not file:
        #     return Response({'msg': '请上传文件'}, status=status.HTTP_400_BAD_REQUEST)
        #
        # # 限制文件类型为json
        # # if not file.name.endswith('.json'):
        # #     return Response({'msg': '文件类型错误'}, status=status.HTTP_400_BAD_REQUEST)
        # # 限制文件大小
        # if file.size > 1024 * 1024 * 10:
        #     return Response({'msg': '文件大小不能超过10M'}, status=status.HTTP_400_BAD_REQUEST)
        #
        # file_name = file.name
        # # 避免文件名重复
        # while default_storage.exists(os.path.join(settings.MEDIA_ROOT, 'file', file_name)):
        #     file_name = f'{os.path.splitext(file_name)[0]}_copy{os.path.splitext(file_name)[1]}'
        # file.name = file_name
        #
        # obj = models.File.objects.create(file=file, user=user)
        #
        # return Response({'msg': '上传成功', 'file_path': obj.file.url}, status=status.HTTP_200_OK)

    # 删除文件
    def delete(self, request):
        file_path = request.data.get('file_path')
        if not file_path:
            return Response({'msg': '请传入文件路径'}, status=status.HTTP_400_BAD_REQUEST)

        # 检查文件路径是否在媒体目录中
        if not file_path.startswith(settings.MEDIA_URL):
            return Response({'msg': '文件路径不在媒体目录中'}, status=status.HTTP_400_BAD_REQUEST)

        # 提取相对路径，并删除开头的'/media/'部分
        relative_file_path = file_path[len(settings.MEDIA_URL):]

        models.File.objects.filter(file=relative_file_path).delete()
        # 使用媒体根目录构建完整的文件路径
        absolute_file_path = os.path.join(settings.MEDIA_ROOT, relative_file_path)

        # 删除文件
        if default_storage.exists(absolute_file_path):
            default_storage.delete(absolute_file_path)
            return Response({'msg': '删除成功'}, status=status.HTTP_200_OK)
        else:
            return Response({'msg': '文件不存在'}, status=status.HTTP_400_BAD_REQUEST)

    # 获取文件内容
    def get(self, request):
        user_id = request.user.id
        user = models.User.objects.get(id=user_id)
        #         获取所有文件路径
        files = models.File.objects.filter(user=user)
        file_list = []
        for file in files:
            file_list.append({
                'file_path': file.file.url,
                'name': file.file.name.split('\\')[-1],
                'time': file.time
            })
        return Response(file_list, status=status.HTTP_200_OK)


class TextALL(APIView):
    def get(self, request):
        user_id = request.user.id
        texts = models.Text.objects.filter(user_id=user_id)
        ret = []
        for text in texts:
            foo = {
                'id': text.id,
                'name': text.name,
                'size': text.size,
                'time': text.time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            ret.append(foo)
        return Response({"texts": ret}, status=status.HTTP_200_OK)

class Text(APIView):
    def get(self, request):
        user_id = request.user.id
        text_id = request.query_params.get('text_id')
        if not text_id:
            return Response({'msg': '请输入文章id'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            text = models.Text.objects.get(id=text_id, user_id=user_id)
            ret = {
                'name': text.name,
                'content': text.content,
                'time': text.time.strftime('%Y-%m-%d %H:%M:%S'),
            }

            return Response(ret, status=status.HTTP_200_OK)
        except models.Text.DoesNotExist:
            return Response({'msg': '文章不存在'}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        user_id = request.user.id
        user = models.User.objects.get(id=user_id)
        data = request.data
        content = data.get('content')
        if not content:
            return Response({'msg': '请输入内容'}, status=status.HTTP_400_BAD_REQUEST)
        name = data.get('name')
        if not name:
            return Response({'msg': '请输入文章名称'}, status=status.HTTP_400_BAD_REQUEST)
        size = len(content)
        location_type = data.get('location_type')
        if location_type == 0:
            # 处理name冲突
            while models.Text.objects.filter(name=name, user=user).exists():
                name = f'{name}_copy'


            text = models.Text.objects.create(content=content, user=user, name=name, size=size, location_type=location_type)
            return Response({'msg': '上传成功', 'id': text.id}, status=status.HTTP_200_OK)
        elif location_type == 1:
            location = data.get('location')
            if not location:
                return Response({'msg': '请输入文章位置'}, status=status.HTTP_400_BAD_REQUEST)
            text = models.Text.objects.create(user=user, name=name, size=size, location=location, location_type=location_type)
            return Response({'msg': '上传成功', 'id':text.id}, status=status.HTTP_200_OK)
        else:
            return Response({'msg': '请输入正确的文章保存类型'}, status=status.HTTP_400_BAD_REQUEST)



    def delete(self, request):
        user_id = request.user.id
        text_id = request.data.get('text_id')
        try:
            text = models.Text.objects.get(id=text_id, user_id=user_id)
            text.delete()
            return Response({'msg': '删除成功'}, status=status.HTTP_200_OK)
        except models.Text.DoesNotExist:
            return Response({'msg': '文章不存在'}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        user_id = request.user.id
        text_id = request.data.get('text_id')
        update_type = request.data.get('update_type')
        if update_type == 'name':
            name = request.data.get('name')
            if not name:
                return Response({'msg': '请输入文章名称'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                # 处理name冲突
                while models.Text.objects.filter(name=name, user_id=user_id).exists():
                    name = f'{name}_copy'

                text = models.Text.objects.get(id=text_id, user_id=user_id)
                text.name = name
                text.save()
                return Response({'msg': '修改成功'}, status=status.HTTP_200_OK)
            except models.Text.DoesNotExist:
                return Response({'msg': '文章不存在'}, status=status.HTTP_400_BAD_REQUEST)
        elif update_type == 'content':
            content = request.data.get('content')
            if not content:
                return Response({'msg': '请输入内容'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                text = models.Text.objects.get(id=text_id, user_id=user_id)
                text.content = content
                text.size = len(content)
                text.save()
                return Response({'msg': '修改成功'}, status=status.HTTP_200_OK)
            except models.Text.DoesNotExist:
                return Response({'msg': '文章不存在'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'msg': '请输入修改类型'}, status=status.HTTP_400_BAD_REQUEST)

class Photo(APIView):
    parser_classes = [MultiPartParser, JSONParser]

    def post(self, request):
        user_id = request.user.id
        user = models.User.objects.get(id=user_id)
        photo = request.data.get('photo')
        if not photo:
            return Response({'msg': '请上传照片'}, status=status.HTTP_400_BAD_REQUEST)

        # 限制文件大小
        if photo.size > 1024 * 1024 * 2:
            return Response({'msg': '文件大小不能超过2M'}, status=status.HTTP_400_BAD_REQUEST)

        photo_name = photo.name
        # 避免文件名重复，使用uuid
        import uuid
        while default_storage.exists(os.path.join(settings.MEDIA_ROOT, 'photo', photo_name)):
            photo_name = f'{uuid.uuid4()}{os.path.splitext(photo_name)[1]}'


            # photo_name = f'{os.path.splitext(photo_name)[0]}_copy{os.path.splitext(photo_name)[1]}'
        photo.name = photo_name

        obj = models.Photo.objects.create(photo=photo, user=user)

        return Response({'msg': '上传成功', 'photo_path': obj.photo.url}, status=status.HTTP_200_OK)

    # 删除照片
    def delete(self, request):
        photo_path = request.data.get('photo_path')
        if not photo_path:
            return Response({'msg': '请传入照片路径'}, status=status.HTTP_400_BAD_REQUEST)

        # 检查照片路径是否在媒体目录中
        if not photo_path.startswith(settings.MEDIA_URL):
            return Response({'msg': '照片路径不在媒体目录中'}, status=status.HTTP_400_BAD_REQUEST)

        # 提取相对路径，并删除开头的'/media/'部分
        relative_photo_path = photo_path[len(settings.MEDIA_URL):]

        models.Photo.objects.filter(photo=relative_photo_path).delete()
        # 使用媒体根目录构建完整的照片路径
        absolute_photo_path = os.path.join(settings.MEDIA_ROOT, relative_photo_path)

        # 删除照片
        if default_storage.exists(absolute_photo_path):
            default_storage.delete(absolute_photo_path)
            return


# 上传音频文件
class Audio(APIView):
    parser_classes = [MultiPartParser, JSONParser]

    def post(self, request):
        user_id = request.user.id
        user = models.User.objects.get(id=user_id)
        audio = request.data.get('audio')
        if not audio:
            return Response({'msg': '请上传音频'}, status=status.HTTP_400_BAD_REQUEST)

        # 限制文件大小
        if audio.size > 1024 * 1024 * 10:
            return Response({'msg': '文件大小不能超过10M'}, status=status.HTTP_400_BAD_REQUEST)

        audio_name = audio.name
        # 避免文件名重复
        while default_storage.exists(os.path.join(settings.MEDIA_ROOT, 'audio', audio_name)):
            audio_name = f'{os.path.splitext(audio_name)[0]}_copy{os.path.splitext(audio_name)[1]}'
        audio.name = audio_name

        obj = models.Audio.objects.create(audio=audio, user=user)

        return Response({'msg': '上传成功', 'audio_path': obj.audio.url}, status=status.HTTP_200_OK)

    # 删除音频
    def delete(self, request):
        audio_path = request.data.get('audio_path')
        if not audio_path:
            return Response({'msg': '请传入音频路径'}, status=status.HTTP_400_BAD_REQUEST)

        # 检查音频路径是否在媒体目录中
        if not audio_path.startswith(settings.MEDIA_URL):
            return Response({'msg': '音频路径不在媒体目录中'}, status=status.HTTP_400_BAD_REQUEST)

        # 提取相对路径，并删除开头的'/media/'部分
        relative_audio_path = audio_path[len(settings.MEDIA_URL):]

        models.Audio.objects.filter(audio=relative_audio_path).delete()
        # 使用媒体根目录构建完整的音频路径
        absolute_audio_path = os.path.join(settings.MEDIA_ROOT, relative_audio_path)

        # 删除音频
        if default_storage.exists(absolute_audio_path):
            default_storage.delete(absolute_audio_path)
            return Response({'msg': '删除成功'}, status=status.HTTP_200_OK)
        else:
            return Response({'msg': '音频不存在'}, status=status.HTTP_400_BAD_REQUEST)

