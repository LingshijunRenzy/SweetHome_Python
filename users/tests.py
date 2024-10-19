import unittest

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from .models import User
from rest_framework.utils import json

from users.views import UserViewJson

class TestUserRegisterJson(TestCase):
    def setUp(self):
        # 设置测试环境
        self.factory = RequestFactory()
        self.user_view = UserViewJson()
        self.user_view.request = None  # 模拟请求对象
        self.user_data = {
            'username': 'newuser',
            'password': 'newpassword',
            'email': 'newuser@example.com'
        }


    # 测试用户注册
    def test_user_register_json(self):
        request = self.factory.post('/register/', data=self.user_data, content_type='application/json')
        request.user = AnonymousUser()  # 模拟未登录用户

        response = self.user_view.user_register_json(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {'message': 'Register Successful'})



    # 测试缺少字段的注册请求
    def test_user_register_json_missing_fields(self):
        request = self.factory.post('/register/', content_type='application/json', data=json.dumps({'username': 'testuser', 'password': 'testpass123'}), user=AnonymousUser())
        response = self.user_view.user_register_json(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {'message': 'Invalid Request: Missing username, password or email'})



    # 测试无效的JSON格式
    def test_user_register_json_invalid_json(self):
        request = self.factory.post('/register/', content_type='application/json', data='invalid json',
                                    user=AnonymousUser())
        response = self.user_view.user_register_json(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {'message': 'Invalid Request: Invalid JSON'})



    # 测试已存在的用户名
    def test_user_register_json_username_exists(self):
        # 创建一个已存在的用户名
        User.objects.create_user(username='newuser', password='testpass123', email='existing@example.com')
        request = self.factory.post('/register/', content_type='application/json', data=json.dumps(self.user_data),
                                    user=AnonymousUser())
        response = self.user_view.user_register_json(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {'message': 'Invalid Request: Username: newuser already exists'})



    # 测试 GET 请求
    def test_user_register_json_get_request(self):
        request = self.factory.get('/register/', user=AnonymousUser())
        response = self.user_view.user_register_json(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {'message': 'Invalid Request: Require method POST, current: GET'})


# 运行测试用例
if __name__ == '__main__':
    unittest.main()
