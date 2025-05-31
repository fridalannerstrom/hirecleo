from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('jobad/', views.jobad, name='jobad'),
    path('login/', auth_views.LoginView.as_view(template_name='auth-login-basic.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('account/', views.account_profile, name='account_profile'),
    path('your-jobs/', views.your_jobs, name='your_jobs'),
    path('add-jobs-manually/', views.add_jobs_manually, name='add_jobs_manually'),
    path('add-jobs-pdf/', views.add_jobs_pdf, name='add_jobs_pdf'),
    path('chat/', views.chat, name='chat'),
    path('skapa-konto/', views.RegisterView.as_view(), name='register'),
    path('job/<slug:slug>/', views.job_detail, name='job_detail'),
    path('job/delete/<slug:slug>/', views.delete_job, name='delete_job'),
    path('job/<slug:slug>/edit/', views.edit_job, name='edit_job'),
    path('jobads/create/', views.create_jobad, name='create_jobad'),
    path('api/generate-jobad/', views.generate_jobad_api, name='generate_jobad_api'),
    path("compare-candidates/", views.compare_candidates_page, name="compare_candidates"),
    path("compare-candidates/api/", views.compare_candidates_api, name="compare_candidates_api"),
    path('testtolkare/upload/', views.upload_test_result, name='upload_test_result'),
    path('testtolkare/result/<int:pk>/', views.test_result_detail, name='test_result_detail'),
    path("testtolkare/api/stream/<int:pk>/", views.testtolkare_stream_response, name="testtolkare_stream"),
]