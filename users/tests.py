import unittest

from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase, RequestFactory
from rest_framework.utils import json

from users.views import *
from .models import User


# 单元测试用例

# 用户注册
class TestUserRegisterJson(TestCase):
    def setUp(self):
        # 设置测试环境
        self.factory = RequestFactory()
        self.request = None  # 模拟请求对象
        self.user_data = {
            'username': 'newuser',
            'password': 'newpassword',
            'email': 'newuser@example.com'
        }


    # 测试用户注册
    def test_user_register_json(self):
        request = self.factory.post('/register/', data=self.user_data, content_type='application/json')
        request.user = AnonymousUser()  # 模拟未登录用户

        response = user_register_json(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {'message': 'Register Successful'})



    # 测试缺少字段的注册请求
    def test_user_register_json_missing_fields(self):
        request = self.factory.post('/register/', content_type='application/json', data=json.dumps({'username': 'testuser', 'password': 'testpass123'}), user=AnonymousUser())
        response = user_register_json(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {'message': 'Invalid Request: Missing username, password or email'})



    # 测试无效的JSON格式
    def test_user_register_json_invalid_json(self):
        request = self.factory.post('/register/', content_type='application/json', data='invalid json',
                                    user=AnonymousUser())
        response = user_register_json(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {'message': 'Invalid Request: Invalid JSON'})



    # 测试已存在的用户名
    def test_user_register_json_username_exists(self):
        # 创建一个已存在的用户名
        User.objects.create_user(username='newuser', password='testpass123', email='existing@example.com')
        request = self.factory.post('/register/', content_type='application/json', data=json.dumps(self.user_data),
                                    user=AnonymousUser())
        response = user_register_json(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {'message': 'Invalid Request: Username: newuser already exists'})



    # 测试 GET 请求
    def test_user_register_json_get_request(self):
        request = self.factory.get('/register', user=AnonymousUser())
        response = user_register_json(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {'message': 'Invalid Request: Require method POST, current: GET'})



class UserLoginJsonTestCase(TestCase):
    def setUp(self):
        # 设置测试环境
        self.factory = RequestFactory()
        self.username = 'testuser'
        self.password = 'testpass123'
        # 创建测试用户
        self.user = User.objects.create_user(username=self.username, password=self.password)

    def test_user_login_json_post_valid(self):
        # 测试有效的POST登录
        request = self.factory.post('/login', {'username': self.username, 'password': self.password},
                                    content_type='application/json')
        request.user = AnonymousUser()
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()

        response = user_login_json(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {'message': 'Login Successful'})

    def test_user_login_json_post_invalid(self):
        # 测试无效的POST登录（用户名或密码错误）
        request = self.factory.post('/login', {'username': 'wronguser', 'password': 'wrongpass'},
                                    content_type='application/json')
        request.user = AnonymousUser()

        response = user_login_json(request)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(json.loads(response.content), {'message': 'Login Failed: User not found'})

    def test_user_login_json_get(self):
        # 测试GET请求
        request = self.factory.get('/login')
        request.user = AnonymousUser()

        response = user_login_json(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content),
                         {'message': 'Invalid Request: Require method POST, current: GET'})



class UserLogoutJsonTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')

    def test_user_logout_json_post_authenticated(self):
        request = self.factory.post('/logout')
        request.user = self.user

        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)

        response = user_logout_json(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {'message': 'Logout Successful'})

    def test_user_logout_json_get_request(self):
        request = self.factory.get('/logout')
        request.user = self.user
        response = user_logout_json(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {'message': 'Invalid Request: Require method POST, current: GET'})

    def test_user_logout_json_post_unauthenticated(self):
        request = self.factory.post('/logout')
        request.user = AnonymousUser()
        response = user_logout_json(request)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(json.loads(response.content), {'message': 'Logout Failed: User not logged in'})



class UserInfoJsonTestCase(TestCase):
    def setUp(self):
        # 设置测试环境
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')
        self.user.is_staff = False
        self.user.save()

        self.staff_user = User.objects.create_user(username='staffuser', email='staff@example.com', password='staffpassword')
        self.staff_user.is_staff = True
        self.staff_user.save()

    def test_user_info_json_get(self):
        # 测试GET方法
        request = self.factory.get('/users/info/testuser/')
        request.user = AnonymousUser()  # 模拟未登录用户
        response = user_info_json(request, self.user.username)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content).get('username'), self.user.username)

    def test_user_info_json_patch_by_owner(self):
        # 测试PATCH方法，当前登录用户是目标用户
        request = self.factory.patch('/users/info/testuser/', content_type='application/json', data=json.dumps({'bio': 'new bio'}))
        request.user = self.user  # 模拟登录用户
        response = user_info_json(request, self.user.username)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, 'new bio')

    def test_user_info_json_patch_by_staff(self):
        # 测试PATCH方法，当前登录用户是staff
        request = self.factory.patch('/users/info/testuser/', content_type='application/json', data=json.dumps({'bio': 'new bio by staff'}))
        request.user = self.staff_user  # 模拟登录用户是staff
        response = user_info_json(request, self.user.username)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, 'new bio by staff')

    def test_user_info_json_patch_by_another_user(self):
        # 测试PATCH方法，当前登录用户是其他非staff用户
        another_user = User.objects.create_user(username='anotheruser', email='another@example.com', password='anotherpassword')
        request = self.factory.patch('/users/info/testuser/', content_type='application/json', data=json.dumps({'bio': 'new bio by another user'}))
        request.user = another_user  # 模拟登录用户是another_user
        response = user_info_json(request, self.user.username)
        self.assertEqual(response.status_code, 403)

    def test_user_info_json_user_not_found(self):
        # 测试用户不存在的情况
        request = self.factory.get('/users/info/nonexistentuser/')
        request.user = AnonymousUser()
        response = user_info_json(request, 'nonexistentuser')
        self.assertEqual(response.status_code, 404)

    def test_user_info_json_invalid_request(self):
        # 测试无效请求
        request = self.factory.post('/users/info/testuser/')
        request.user = AnonymousUser()
        response = user_info_json(request, self.user.username)
        self.assertEqual(response.status_code, 400)


class UserDeleteJsonTestCase(TestCase):
    def setUp(self):
        # 设置测试环境
        self.factory = RequestFactory()
        self.username = 'testuser'
        self.password = 'secret'
        self.user = User.objects.create_user(username=self.username, password=self.password)

    def test_user_delete_json_with_delete_method(self):
        # 测试使用DELETE方法删除用户
        request = self.factory.delete('/delete')
        request.user = self.user

        response = user_delete_json(request, self.username)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {'message': 'User deleted successfully'})
        self.assertFalse(User.objects.filter(username=self.username).exists())

    def test_user_delete_json_with_non_delete_method(self):
        # 测试使用非DELETE方法
        request = self.factory.get('/delete')
        request.user = self.user

        response = user_delete_json(request, self.username)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {'message': 'Invalid Request: Require method DELETE, current: GET'})

    def test_user_delete_json_with_unauthenticated_user(self):
        # 测试未认证用户尝试删除用户
        request = self.factory.delete('/delete')
        request.user = AnonymousUser()

        response = user_delete_json(request, self.username)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(json.loads(response.content), {'message': 'User not logged in'})

    def test_user_delete_json_with_permission_denied(self):
        # 测试权限被拒绝的情况（非管理员和非目标用户）
        another_user = User.objects.create_user(username='anotheruser', password='secret')
        request = self.factory.delete('/delete')
        request.user = another_user

        response = user_delete_json(request, self.username)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(json.loads(response.content), {'message': 'Permission denied'})

    def test_user_delete_json_with_nonexistent_user(self):
        # 测试尝试删除不存在的用户
        request = self.factory.delete('/delete')
        request.user = self.user

        response = user_delete_json(request, 'nonexistentuser')
        self.assertEqual(response.status_code, 403)
# 运行测试用例
if __name__ == '__main__':
    unittest.main()
