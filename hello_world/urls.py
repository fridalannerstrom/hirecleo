from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='auth-login-basic.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('account/', views.account_profile, name='account_profile'),
    path('chat/', views.chat, name='chat'),
    path('skapa-konto/', views.RegisterView.as_view(), name='register'),
]