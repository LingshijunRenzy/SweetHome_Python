from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

app_name = 'users'

urlpatterns = [
    path('login',views.user_login_json),
    path('logout',views.user_logout_json),
    path('register', csrf_exempt(views.user_register_json)),
    path('<str:username>', views.user_info_json),
    path('<str:username>/delete',views.user_delete_json),
]