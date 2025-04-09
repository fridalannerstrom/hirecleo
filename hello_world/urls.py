from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('candidates/', views.candidates, name='candidates'),
    path('jobs/', views.jobs, name='jobs'),
    path('upload-candidates/', views.upload_candidates, name='upload_candidates'),
    path('upload-jobs/', views.upload_jobs, name='upload_jobs'),
    path('jobad/', views.jobad, name='jobad'),
    path('login/', auth_views.LoginView.as_view(template_name='auth-login-basic.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('account/', views.account_profile, name='account_profile'),
]