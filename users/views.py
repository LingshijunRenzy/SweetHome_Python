import json

from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import viewsets, mixins, serializers, permissions
from rest_framework.decorators import action

from common.signals import UserSignals
from users.models import User
from users.permissions import IsStaffOrAuthor
from users.serializers import UserSerializer, UserRequestSerializer


# Create your views here.

class UserViewSet(mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  mixins.DestroyModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated, IsStaffOrAuthor]
        return super().get_permissions()

    @extend_schema(
        description='用户登录接口\n完成登录后，会在返回的cookie中携带sessionid, 作为下次登录的凭证，后续请求时需要携带此cookie',
        summary='用户登录',
        request=inline_serializer(
            name='UserLoginRequest',
            fields={
                'username': serializers.CharField(help_text='用户名'),
                'password': serializers.CharField(help_text='密码')
            }
        ),
    )
    @action(detail=False, methods=['POST'])
    def login(self, request):
        try:
            data = request.data
        except json.JSONDecodeError:
            return JsonResponse({'message': 'Invalid Request: Invalid JSON'}, status=400)
        username = data.get('username')
        password = data.get('password')
        user = authenticate(request, username=username, password=password)  # 调用 django 的 authenticate 方法
        if user is not None:
            login(request, user)  # 调用 django 的 login 方法
            UserSignals.on_user_logged_in.send(sender=user)
            return JsonResponse({'message': 'Login Successful'}, status=200)
        return JsonResponse({'message': 'Login Failed: User not found'}, status=401)



    @extend_schema(
        summary='用户注册',
        description='用户注册接口\n用户注册成功后，会自动完成一次登录操作',
        request=UserRequestSerializer
    )
    @action(detail=False, methods=['POST'])
    def register(self, request):
        try:
            data = request.data
            # data = request.POST.dict()
            username = data.get('username')
            password = data.get('password')
            nickname = data.get('nickname')
            email = data.get('email')
        except json.JSONDecodeError:
            return JsonResponse({'message': 'Invalid Request: Invalid JSON'}, status=400)

        if not username or not password or not email:
            return JsonResponse({'message': 'Invalid Request: Missing username, password or email'}, status=400)

        # 检查用户名是否已存在
        if User.objects.filter(username=username).exists():
            return JsonResponse({'message': 'Invalid Request: Username: ' + username +' already exists'}, status=400)

        user_data = {
            'username': username,
            'password': make_password(password),
            'email': email if email else None,
            'nickname': nickname if nickname else username
        }

        user_serializer = UserSerializer(data=user_data)
        if user_serializer.is_valid():
            user = user_serializer.save()
            login(request, user)
            UserSignals.on_user_registered.send(sender=user)
            return JsonResponse({'message': 'Register Successful'}, status=200)
        else:
            return JsonResponse({'message': 'Invalid Request: ' + str(user_serializer.errors)}, status=400)