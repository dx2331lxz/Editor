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



# 登录
class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        data = request.data
        try:
            user = User.objects.get(username=data.get('username'))
            if not user.check_password(data.get('password')):
                return Response({'msg': '密码错误'}, status=status.HTTP_400_BAD_REQUEST)

            if request.META.get('HTTP_X_FORWARDED_FOR'):
                ip = request.META.get("HTTP_X_FORWARDED_FOR")
            else:
                ip = request.META.get("HTTP_X_REAL_IP")
            if not ip:
                if 'HTTP_X_FORWARDED_FOR' in request.META:
                    ip = request.META.get('HTTP_X_FORWARDED_FOR')
                else:
                    ip = request.META.get('REMOTE_ADDR')
            if models.LoginRecord.objects.filter(user=user, ip=ip).exists():
            #     查看是否过期
                login_record = models.LoginRecord.objects.filter(user=user, ip=ip).first()
                if login_record.login_time + timezone.timedelta(days=7) < timezone.now():
            #         过期则需要手机号验证码登录
                    return Response({'msg': '登录过期，请使用手机号验证码登录'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'msg': f'当前地址{ip}为新地址登录，请使用手机号验证码登录'}, status=status.HTTP_400_BAD_REQUEST)
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })

        except User.DoesNotExist:
            return Response({'msg': '用户不存在'}, status=status.HTTP_400_BAD_REQUEST)





# 修改密码
class ChangePassword(APIView):
    def get(self, request):
        user_id = request.user.id
        user = User.objects.get(id=user_id)
        # 发送验证码
        phone_number = user.username
        resp, verification_code = SendSMSVerificationCode().send_sms(phone_number)
        ## todo 添加发送短信是否成功的逻辑
        if resp.SendStatusSet[0].Code == 'Ok':
            # 记录生成时间和过期时间（60秒后）
            expiration_time = timezone.now() + timezone.timedelta(minutes=10)

            # 保存验证码到数据库
            models.PhoneVerification.objects.update_or_create(
                phone_number=phone_number,
                defaults={'verification_code': verification_code, 'expiration_time': expiration_time}
            )
            return Response({'msg': 'Verification code sent'})
        else:
            return Response({'msg': f'发送失败,出了点小问题{resp.SendStatusSet[0].Code}', 'code': 403},
                            status=status.HTTP_403_FORBIDDEN)

    def post(self, request):
        user_id = request.user.id
        user = User.objects.get(id=user_id)
        data = request.data
        verification_code = data.get('verification_code')
        if not verification_code:
            return Response({'msg': '请输入验证码'}, status=status.HTTP_400_BAD_REQUEST)
        phone_number = user.username
        try:
            verification = models.PhoneVerification.objects.get(phone_number=phone_number)
        except models.PhoneVerification.DoesNotExist:
            return Response({'msg': '验证码失效，请重新发送验证码'}, status=400)

        now = timezone.now()
        if verification.expiration_time >= now and verification.verification_code == verification_code:
            new_password = data.get('new_password')
            score = Register().check_password(new_password)
            if score < 50:
                return Response({'msg': '密码强度不够'}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.save()
            return Response({'msg': '修改密码成功'}, status=status.HTTP_200_OK)
        else:
            return Response({'msg': '验证码错误或已超时'}, status=400)


# 上传头像
class Avatar(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        user_id = request.user.id
        user = User.objects.get(id=user_id)
        avatar = request.FILES.get('avatar')
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


import random
from Editor import settings
## 引入腾讯云短信
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
# 导入对应产品模块的client models。
from tencentcloud.sms.v20210111 import sms_client
from tencentcloud.sms.v20210111.models import SendSmsRequest
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
# 导入时区
from django.utils import timezone
class SendSMSVerificationCode(APIView):
    permission_classes = [AllowAny]
    def send_sms(self, phone):
        # 生成随机的验证码
        verification_code = str(random.randint(100000, 999999))
        while True:
            if models.PhoneVerification.objects.filter(verification_code=verification_code).exists():
                verification_code = str(random.randint(100000, 999999))
            else:
                break
        # 发送验证码逻辑
        print(verification_code)
        try:
            # 必要步骤:
            # 实例化一个认证对象，入参需要传入腾讯云账户密钥对secretId，secretKey。
            # 这里采用的是从环境变量读取的方式，需要在环境变量中先设置这两个值。
            # 您也可以直接在代码中写死密钥对，但是小心不要将代码复制、上传或者分享给他人，
            # 以免泄露密钥对危及您的财产安全。
            # SecretId、SecretKey 查询: https://console.cloud.tencent.com/cam/capi
            cred = credential.Credential(settings.SecretId, settings.SecretKey)

            # 实例化一个http选项，可选的，没有特殊需求可以跳过。
            httpProfile = HttpProfile()
            # 如果需要指定proxy访问接口，可以按照如下方式初始化hp（无需要直接忽略）
            # httpProfile = HttpProfile(proxy="http://用户名:密码@代理IP:代理端口")
            httpProfile.reqMethod = "POST"  # post请求(默认为post请求)
            httpProfile.reqTimeout = 30  # 请求超时时间，单位为秒(默认60秒)
            httpProfile.endpoint = "sms.tencentcloudapi.com"  # 指定接入地域域名(默认就近接入)

            # 非必要步骤:
            # 实例化一个客户端配置对象，可以指定超时时间等配置
            clientProfile = ClientProfile()
            clientProfile.signMethod = "TC3-HMAC-SHA256"  # 指定签名算法
            clientProfile.language = "zh-CN"
            clientProfile.httpProfile = httpProfile

            # 实例化要请求产品(以sms为例)的client对象
            # 第二个参数是地域信息，可以直接填写字符串ap-guangzhou，支持的地域列表参考 https://cloud.tencent.com/document/api/382/52071#.E5.9C.B0.E5.9F.9F.E5.88.97.E8.A1.A8
            client = sms_client.SmsClient(cred, "ap-beijing", clientProfile)

            # 实例化一个请求对象，根据调用的接口和实际情况，可以进一步设置请求参数
            # 您可以直接查询SDK源码确定SendSmsRequest有哪些属性可以设置
            # 属性可能是基本类型，也可能引用了另一个数据结构
            # 推荐使用IDE进行开发，可以方便的跳转查阅各个接口和数据结构的文档说明
            req = SendSmsRequest()

            # 基本类型的设置:
            # SDK采用的是指针风格指定参数，即使对于基本类型您也需要用指针来对参数赋值。
            # SDK提供对基本类型的指针引用封装函数
            # 帮助链接：
            # 短信控制台: https://console.cloud.tencent.com/smsv2
            # 腾讯云短信小助手: https://cloud.tencent.com/document/product/382/3773#.E6.8A.80.E6.9C.AF.E4.BA.A4.E6.B5.81

            # 短信应用ID: 短信SdkAppId在 [短信控制台] 添加应用后生成的实际SdkAppId，示例如1400006666
            # 应用 ID 可前往 [短信控制台](https://console.cloud.tencent.com/smsv2/app-manage) 查看
            req.SmsSdkAppId = "1400805669"
            # 短信签名内容: 使用 UTF-8 编码，必须填写已审核通过的签名
            # 签名信息可前往 [国内短信](https://console.cloud.tencent.com/smsv2/csms-sign) 或 [国际/港澳台短信](https://console.cloud.tencent.com/smsv2/isms-sign) 的签名管理查看
            req.SignName = "高坂滑稽果的学习笔记网"
            # 模板 ID: 必须填写已审核通过的模板 ID
            # 模板 ID 可前往 [国内短信](https://console.cloud.tencent.com/smsv2/csms-template) 或 [国际/港澳台短信](https://console.cloud.tencent.com/smsv2/isms-template) 的正文模板管理查看
            req.TemplateId = "1743214"
            # 模板参数: 模板参数的个数需要与 TemplateId 对应模板的变量个数保持一致，，若无模板参数，则设置为空
            req.TemplateParamSet = [verification_code, '10']
            # 下发手机号码，采用 E.164 标准，+[国家或地区码][手机号]
            # 示例如：+8613711112222， 其中前面有一个+号 ，86为国家码，13711112222为手机号，最多不要超过200个手机号
            req.PhoneNumberSet = [f"+86{phone}"]
            # 用户的 session 内容（无需要可忽略）: 可以携带用户侧 ID 等上下文信息，server 会原样返回
            req.SessionContext = ""
            # 短信码号扩展号（无需要可忽略）: 默认未开通，如需开通请联系 [腾讯云短信小助手]
            req.ExtendCode = ""
            # 国内短信无需填写该项；国际/港澳台短信已申请独立 SenderId 需要填写该字段，默认使用公共 SenderId，无需填写该字段。注：月度使用量达到指定量级可申请独立 SenderId 使用，详情请联系 [腾讯云短信小助手](https://cloud.tencent.com/document/product/382/3773#.E6.8A.80.E6.9C.AF.E4.BA.A4.E6.B5.81)。
            req.SenderId = ""

            resp = client.SendSms(req)
            return resp, verification_code
        except TencentCloudSDKException as err:
            # 当出现以下错误码时，快速解决方案参考
            # - [FailedOperation.SignatureIncorrectOrUnapproved](https://cloud.tencent.com/document/product/382/9558#.E7.9F.AD.E4.BF.A1.E5.8F.91.E9.80.81.E6.8F.90.E7.A4.BA.EF.BC.9Afailedoperation.signatureincorrectorunapproved-.E5.A6.82.E4.BD.95.E5.A4.84.E7.90.86.EF.BC.9F)
            # - [FailedOperation.TemplateIncorrectOrUnapproved](https://cloud.tencent.com/document/product/382/9558#.E7.9F.AD.E4.BF.A1.E5.8F.91.E9.80.81.E6.8F.90.E7.A4.BA.EF.BC.9Afailedoperation.templateincorrectorunapproved-.E5.A6.82.E4.BD.95.E5.A4.84.E7.90.86.EF.BC.9F)
            # - [UnauthorizedOperation.SmsSdkAppIdVerifyFail](https://cloud.tencent.com/document/product/382/9558#.E7.9F.AD.E4.BF.A1.E5.8F.91.E9.80.81.E6.8F.90.E7.A4.BA.EF.BC.9Aunauthorizedoperation.smssdkappidverifyfail-.E5.A6.82.E4.BD.95.E5.A4.84.E7.90.86.EF.BC.9F)
            # - [UnsupportedOperation.ContainDomesticAndInternationalPhoneNumber](https://cloud.tencent.com/document/product/382/9558#.E7.9F.AD.E4.BF.A1.E5.8F.91.E9.80.81.E6.8F.90.E7.A4.BA.EF.BC.9Aunsupportedoperation.containdomesticandinternationalphonenumber-.E5.A6.82.E4.BD.95.E5.A4.84.E7.90.86.EF.BC.9F)
            # - 更多错误，可咨询[腾讯云助手](https://tccc.qcloud.com/web/im/index.html#/chat?webAppId=8fa15978f85cb41f7e2ea36920cb3ae1&title=Sms)
            return {'msg': '发送失败,出了点小问题，{}'.format(err)}, None



    def get(self, request):
        phone = request.query_params.get('phone')
        if not phone:
            return Response({'msg': '请输入手机号', 'code': 403}, status=status.HTTP_403_FORBIDDEN)

        # 发送验证码
        resp, verification_code = self.send_sms(phone)
        # 输出json格式的字符串回包
        print(resp.to_json_string(indent=2))
        ## todo 添加发送短信是否成功的逻辑
        if resp.SendStatusSet[0].Code == 'Ok':
            # 记录生成时间和过期时间（60秒后）
            expiration_time = timezone.now() + timezone.timedelta(minutes=10)

            # 保存验证码到数据库
            models.PhoneVerification.objects.update_or_create(
                phone_number=phone,
                defaults={'verification_code': verification_code, 'expiration_time': expiration_time}
            )
            return Response({'msg': 'Verification code sent'})
        else:
            return Response({'msg': f'发送失败,出了点小问题{resp.SendStatusSet[0].Code}', 'code': 403},
                            status=status.HTTP_403_FORBIDDEN)



    def post(self, request):
        phone_number = request.data.get('phone')
        verification_code = request.data.get('verification_code')

        # 在数据库中验证验证码
        if not phone_number or not verification_code:
            return Response({'msg': '电话号码或验证码为空', 'code': 403}, status=status.HTTP_403_FORBIDDEN)
        try:
            verification = models.PhoneVerification.objects.get(phone_number=phone_number)
        except models.PhoneVerification.DoesNotExist:
            return Response({'msg': '验证码失效，请重新发送验证码'}, status=400)

        now = timezone.now()
        if verification.expiration_time >= now and verification.verification_code == verification_code:
            try:
            #     查看是否有这个用户，没有则创建然后登录成功，有则登录成功
                user = User.objects.get(username=phone_number)
            except User.DoesNotExist:
                user = User.objects.create_user(username=phone_number, password=phone_number)
            #     记录登录ip
            if request.META.get('HTTP_X_FORWARDED_FOR'):
                ip = request.META.get("HTTP_X_FORWARDED_FOR")
            else:
                ip = request.META.get("HTTP_X_REAL_IP")
            models.LoginRecord.objects.update_or_create(user=user, defaults={'ip': ip})
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        else:
            return Response({'msg': '验证码错误或已超时'}, status=400)