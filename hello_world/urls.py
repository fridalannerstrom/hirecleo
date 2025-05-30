from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


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
    path('candidates/<slug:slug>/save-test/', views.save_test_to_candidate, name='save_test_to_candidate'),
    path('candidates/create-from-test/', views.create_new_candidate_from_test, name='create_new_candidate_from_test'),
    path("api/find-matching-candidate/", views.find_matching_candidate, name="find_matching_candidate"),
    path("api/save-summary-to-existing/", views.save_summary_to_existing, name="save_summary_to_existing"),
    path("api/save-summary-as-new-candidate/", views.save_summary_as_new_candidate, name="save_summary_as_new_candidate"),
]