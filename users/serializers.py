from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id',
                  'username',
                  'nickname',
                  'email',
                  'is_staff',
                  'is_superuser',
                  'is_active',
                  'last_login',
                  'date_joined',
                  'is_authenticated',
                  'is_anonymous',
                  'avatar_url',
                  'article_count',
                  'comment_count',
                  'like_count',
                  'star_count',
                  'following_count',
                  'follower_count')
        extra_kwargs = {
            'password': {'write_only': True},
            'nickname': {'required': False}
        }
        read_only_fields = ('id',
                            'is_staff',
                            'is_superuser',
                            'is_active',
                            'last_login',
                            'date_joined',
                            'is_authenticated',
                            'is_anonymous',
                            'article_count',
                            'comment_count',
                            'like_count',
                            'star_count',
                            'following_count',
                            'follower_count')

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return User.objects.create(**validated_data)


class UserRequestSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=50, help_text='用户名，唯一标识用户',required=True)
    password = serializers.CharField(max_length=50, help_text='密码',required=True)
    email = serializers.EmailField(help_text='邮箱',required=False)
    nickname = serializers.CharField(max_length=50, help_text='昵称',required=False)