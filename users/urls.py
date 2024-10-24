from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from rest_framework import routers

from . import views

app_name = 'users'

router = routers.DefaultRouter()
router.register(r'', views.UserViewSet)

urlpatterns = [
    # path('login',views.user_login_json),
    # path('logout',views.user_logout_json),
    # path('register', csrf_exempt(views.user_register_json)),
    # path('<str:username>', views.user_info_json),
    # path('<str:username>/delete',views.user_delete_json),

    path('', include(router.urls))
]