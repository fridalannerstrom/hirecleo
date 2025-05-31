from django.urls import path
from . import views

urlpatterns = [
    path('', views.compare_candidates_page, name='compare_candidates'),
    path('api/', views.compare_candidates_api, name='compare_candidates_api'),
]