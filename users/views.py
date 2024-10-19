import json

from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views import View

from common.signals import UserSignals
from users.models import User


# Create your views here.
class UserViewJson(View):
    def user_register_json(self, request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
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

            UserSignals.on_user_registered.send(sender=self, user=user)

            return JsonResponse({'message': 'Register Successful'}, status=200)
        else:
            return JsonResponse({'message': 'Invalid Request: Require method POST, current: ' + request.method}, status=400)



    def user_login_json(self, request):
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password) # 调用 django 的 authenticate 方法
            if user is not None:
                login(request, user) # 调用 django 的 login 方法
                UserSignals.on_user_logged_in.send(sender=self, user=user)
                return JsonResponse({'message': 'Login Successful'}, status=200)
            return JsonResponse({'message': 'Login Failed: User not found'}, status=404)
        else:
            return JsonResponse({'message': 'Invalid Request: Require method POST, current: ' + request.method}, status=400)



    def user_logout_json(self, request):
        if request.method != 'POST':
            return JsonResponse({'message': 'Invalid Request: Require method POST, current: ' + request.method}, status=400)

        if request.user.is_authenticated:
            logout(request)
            UserSignals.on_user_logged_out.send(sender=self, user=request.user)
            return JsonResponse({'message': 'Logout Successful'}, status=200)
        return JsonResponse({'message': 'Logout Failed: User not logged in'}, status=404)



    def user_get_info_json(self, request, username):
        if request.method != 'GET':
            return JsonResponse({'message': 'Invalid Request: Require method GET, current: ' + request.method}, status=400)

        # 根据username查询用户信息
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({'message': 'User not found with username: ' + username}, status=404)

        UserSignals.on_user_info_got.send(sender=self, user=user)
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



    def user_update_info_json(self, request, username):
        # use PATCH method
        if request.method != 'PATCH':
            return JsonResponse({'message': 'Invalid Request: Require method PATCH, current: ' + request.method}, status=400)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({'message': 'User not found with username: ' + username}, status=404)

        try:
            data = request.POST.dict()

            for key, value in data.items():
                if hasattr(user, key):
                    setattr(user, key, value)

            user.save()
            UserSignals.on_user_updated.send(sender=self, user=user)
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

        except ValidationError as e:
            return JsonResponse({'message': str(e)}, status=400)

        except Exception as e:
            return JsonResponse({'message': 'Internal Server Error: ' + str(e)}, status=500)



    def user_delete_json(self, request, username):
        if request.method != 'DELETE':
            return JsonResponse({'message': 'Invalid Request: Require method DELETE, current: ' + request.method}, status=400)

        if not request.user.is_authenticated:
            return JsonResponse({'message': 'User not logged in'}, status=401)

        try:
            user = User.objects.get(username=username)
            user.delete()
            UserSignals.on_user_deleted.send(sender=self, user=user)
            return JsonResponse({'message': 'User deleted successfully'}, status=200)
        except User.DoesNotExist:
            return JsonResponse({'message': 'User not found with username: ' + username}, status=404)
        except Exception as e:
            return JsonResponse({'message': 'Internal Server Error: ' + str(e)}, status=500)