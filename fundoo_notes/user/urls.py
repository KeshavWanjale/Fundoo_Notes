from django.urls import path
from .views import RegisterUser, LoginUser, verify_registered_user

urlpatterns = [
    path('register/', RegisterUser.as_view(), name='register'),
    path('login/', LoginUser.as_view(), name='login'),
    path('verify-user/<str:token>/', verify_registered_user, name='verify_user'),
]