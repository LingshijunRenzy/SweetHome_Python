from django.dispatch import receiver
from common.signals import UserSignals
from users.models import User


@receiver(UserSignals.on_user_article_created)
def handle_article_created(sender, instance, *args, **kwargs):
    # sender=self.__class__,instance=self.request.user self=ArticleViewSet
    # 更新user的article_count字段
    user = User.objects.get(id=instance.id)
    user.article_count += 1
    user.save()

@receiver(UserSignals.on_user_article_deleted)
def handle_article_deleted(sender, instance, *args, **kwargs):
    user = User.objects.get(id=instance.id)
    user.article_count -= 1
    user.save()