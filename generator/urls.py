from django.urls import path
from . import views

urlpatterns = [
    path('', views.create_jobad, name='create_jobad'),
    path('api/generate-jobad/', views.generate_jobad_api, name='generate_jobad_api'),
    path('<int:pk>/', views.jobad_detail, name='jobad_detail'),
]