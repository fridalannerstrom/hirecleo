from django.urls import path
from . import views

urlpatterns = [
    path('your-jobs/', views.your_jobs, name='your_jobs'),
    path('add-jobs-manually/', views.add_jobs_manually, name='add_jobs_manually'),
    path('add-jobs-pdf/', views.add_jobs_pdf, name='add_jobs_pdf'),

    path('<slug:slug>/edit/', views.edit_job, name='edit_job'),
    path('<slug:slug>/delete/', views.delete_job, name='delete_job'),
    path('<slug:slug>/', views.job_detail, name='job_detail'), 
]