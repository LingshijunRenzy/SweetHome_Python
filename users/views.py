import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import viewsets, mixins, serializers
from rest_framework.decorators import action

from common.signals import UserSignals
from users.models import User
from users.serializers import UserSerializer, UserRequestSerializer


# Create your views here.
def user_register_json(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # data = request.POST.dict()
            username = data.get('username')
            password = data.get('password')
            email = data.get('email')
        except json.JSONDecodeError:
            return JsonResponse({'message': 'Invalid Request: Invalid JSON'}, status=400)

        if not username or not password or not email:
            return JsonResponse({'message': 'Invalid Request: Missing username, password or email'}, status=400)

        # 检查用户名是否已存在
        if User.objects.filter(username=username).exists():
            return JsonResponse({'message': 'Invalid Request: Username: ' + username +' already exists'}, status=400)

        user = User.objects.create_user(username=username, password=password, email=email)
        user.save()

        UserSignals.on_user_registered.send(sender=user)

        return JsonResponse({'message': 'Register Successful'}, status=200)
    else:
        return JsonResponse({'message': 'Invalid Request: Require method POST, current: ' + request.method}, status=400)



def user_login_json(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        user = authenticate(request, username=username, password=password) # 调用 django 的 authenticate 方法
        if user is not None:
            login(request, user) # 调用 django 的 login 方法
            UserSignals.on_user_logged_in.send(sender=user)
            return JsonResponse({'message': 'Login Successful'}, status=200)
        return JsonResponse({'message': 'Login Failed: User not found'}, status=404)
    else:
        return JsonResponse({'message': 'Invalid Request: Require method POST, current: ' + request.method}, status=400)



def user_logout_json(request):
    if request.method != 'POST':
        return JsonResponse({'message': 'Invalid Request: Require method POST, current: ' + request.method}, status=400)

    if request.user.is_authenticated:
        logout(request)
        UserSignals.on_user_logged_out.send(sender=request.user)
        return JsonResponse({'message': 'Logout Successful'}, status=200)
    return JsonResponse({'message': 'Logout Failed: User not logged in'}, status=404)



def user_info_json(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'message': 'User not found with username: ' + username}, status=404)

    if request.method == 'GET':
        UserSignals.on_user_info_got.send(sender=user)

    elif request.method == 'PATCH':
        #权限审查
        if not request.user.is_authenticated:
            return JsonResponse({'message': 'User not logged in'}, status=401)
        if user != request.user and not request.user.is_staff:
            return JsonResponse({'message': 'Permission denied'}, status=403)

        try:
            data = json.loads(request.body)
            for key, value in data.items():
                if hasattr(user, key):
                    setattr(user, key, value)

            user.save(update_fields=data.keys())
            UserSignals.on_user_updated.send(sender=user)

        except ValidationError as e:
            return JsonResponse({'message': str(e)}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'message': 'Invalid Request: Invalid JSON'}, status=400)
        except AttributeError:
            return JsonResponse({'message': 'Invalid Request: Invalid attribute'}, status=400)
        except Exception as e:
            return JsonResponse({'message': 'Internal Server Error: ' + str(e)}, status=500)
    else:
        return JsonResponse({'message': 'Invalid Request: Require method GET or PATCH, current: ' + request.method}, status=400)

    return JsonResponse({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'bio': user.bio,
        'avatar_url': user.avatar_url,
        'follower_count': user.follower_count,
        'following_count': user.following_count,
        'article_count': user.article_count,
        'comment_count': user.comment_count,
        'like_count': user.like_count,
    }, status=200)

def user_delete_json(request, username):
    if request.method != 'DELETE':
        return JsonResponse({'message': 'Invalid Request: Require method DELETE, current: ' + request.method}, status=400)

    if not request.user.is_authenticated:
        return JsonResponse({'message': 'User not logged in'}, status=401)

    # 增加检查，只有用户本身和管理员可以删除用户
    if request.user.username != username and not request.user.is_staff:
        return JsonResponse({'message': 'Permission denied'}, status=403)

    try:
        user = User.objects.get(username=username)
        user.delete()
        UserSignals.on_user_deleted.send(sender=username)
        return JsonResponse({'message': 'User deleted successfully'}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'message': 'User not found with username: ' + username}, status=404)
    except Exception as e:
        return JsonResponse({'message': 'Internal Server Error: ' + str(e)}, status=500)

class UserViewSet(mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  mixins.DestroyModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


    @extend_schema(
        description='用户登录接口',
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
        description='用户注册接口',
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