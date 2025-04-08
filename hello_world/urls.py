from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('candidates/', views.candidates, name='candidates'),
    path('jobs/', views.jobs, name='jobs'),
    path('upload-candidates/', views.upload_candidates, name='upload_candidates'),
    path('upload-jobs/', views.upload_jobs, name='upload_jobs'),
    path('jobad/', views.jobad, name='jobad'),
]