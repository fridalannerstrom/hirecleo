# interviewprep/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('forberedelse/', views.prepare_interview, name='prepare_interview'),
]