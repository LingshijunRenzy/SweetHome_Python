from django.shortcuts import render
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import viewsets, serializers, permissions

from articles.models import Article
from articles.permissions import IsStaffOrAuthor
from articles.serializers import ArticleSerializer
from common.signals import UserSignals


# Create your views here.
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticated]

    # 所有用户都可以创建文章，但是只有管理员和作者可以修改和删除文章
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsStaffOrAuthor()]

        if self.action == 'retrieve':
            return []

        return super().get_permissions()

    @extend_schema(
        summary="创建文章",
        description="创建一篇文章",
        request=inline_serializer(
            name="ArticleCreateSerializer",
            fields={
                'title': serializers.CharField(max_length=50,help_text="文章标题"),
                'content': serializers.CharField(help_text="文章内容")
            }
        )
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
        UserSignals.on_user_article_created.send(sender=self.__class__,instance=self.request.user)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="获取文章详情",
        description="获取一篇文章的详细信息",
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="更新文章（整体）",
        description="更新一篇文章，需要传输所有字段",
        request=inline_serializer(
            name="ArticleUpdateSerializer",
            fields={
                'title': serializers.CharField(max_length=50,help_text="文章标题"),
                'content': serializers.CharField(help_text="文章内容")
            }
        )
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="更新文章（局部）",
        description="更新一篇文章，仅传输需要更改的字段",
        request=inline_serializer(
            name="ArticleUpdateSerializer",
            fields={
                'title': serializers.CharField(max_length=50,help_text="文章标题",required=False),
                'content': serializers.CharField(help_text="文章内容",required=False)
            }
        )
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


    def destroy(self, request, *args, **kwargs):
        UserSignals.on_user_article_deleted.send(sender=self.__class__,instance=self.request.user)
        return super().destroy(request, *args, **kwargs)