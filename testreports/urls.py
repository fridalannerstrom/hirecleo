from django.urls import path
from . import views

urlpatterns = [
    path('your-testreports/', views.your_testreports, name='your_testreports'),
    path('upload-testreport/', views.upload_testreport, name='upload_testreport'),
    path('testreport/<int:id>/', views.testreport_detail, name='testreport_detail'),
]