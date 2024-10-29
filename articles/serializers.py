from rest_framework import serializers

from articles.models import Article


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ('id',
                  'title',
                  'content',
                  'created_time',
                  'updated_time',
                  'author',
                  'like_count',
                  'dislike_count',
                  'star_count',
                  'comment_count',
                  'view_count')
        read_only_fields = ('id',
                            'author',
                            'created_time',
                            'updated_time',
                            'like_count',
                            'dislike_count',
                            'star_count',
                            'comment_count',
                            'view_count')

        def create(self, validated_data):
            validated_data['author'] = self.context['request'].user
            return Article.objects.create(**validated_data)