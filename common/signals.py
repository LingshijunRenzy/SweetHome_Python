from django.dispatch import Signal

# 在此处定义信号

class UserSignals:
    on_user_registered = Signal()
    on_user_logged_in = Signal()
    on_user_logged_out = Signal()
    on_user_updated = Signal()
    on_user_deleted = Signal()
    on_user_followed = Signal()
    on_user_unfollowed = Signal()
    on_user_liked = Signal()
    on_user_unliked = Signal()
    on_user_commented = Signal()
    on_user_comment_deleted = Signal()
    on_user_article_created = Signal()
    on_user_article_deleted = Signal()
    on_user_article_liked = Signal()
    on_user_article_unliked = Signal()
    on_user_article_commented = Signal()
    on_user_article_comment_deleted = Signal()
    on_user_article_updated = Signal()
    on_user_article_viewed = Signal()
    on_user_article_shared = Signal()
    on_user_article_shared_deleted = Signal()
    on_user_info_got = Signal()
