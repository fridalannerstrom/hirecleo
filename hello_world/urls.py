from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import RegisterView


urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('jobad/', views.jobad, name='jobad'),
    path('login/', auth_views.LoginView.as_view(template_name='auth-login-basic.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('account/', views.account_profile, name='account_profile'),
    path('add-candidates-manually/', views.add_candidates_manually, name='add_candidates_manually'),
    path('add-candidates-pdf/', views.add_candidates_pdf, name='add_candidates_pdf'),
    path('your-candidates/', views.your_candidates, name='your_candidates'),
    path('your-jobs/', views.your_jobs, name='your_jobs'),
    path('add-jobs-manually/', views.add_jobs_manually, name='add_jobs_manually'),
    path('add-jobs-pdf/', views.add_jobs_pdf, name='add_jobs_pdf'),
    path('chat/', views.chat, name='chat'),
    path('candidates/<slug:slug>/', views.candidate_detail, name='candidate_detail'),
    path('candidates/<slug:slug>/edit/', views.edit_candidate, name='edit_candidate'),
    path('candidates/<slug:slug>/delete/', views.delete_candidate, name='delete_candidate'),
    path('skapa-konto/', RegisterView.as_view(), name='register'),
]