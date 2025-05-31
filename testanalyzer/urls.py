from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_test_result, name='upload_test_result'),
    path('<int:pk>/', views.test_result_detail, name='test_result_detail'),
    path("api/stream/<int:pk>/", views.testtolkare_stream_response, name="testtolkare_stream"),
]