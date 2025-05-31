from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='auth-login-basic.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('account/', views.account_profile, name='account_profile'),
    path('chat/', views.chat, name='chat'),
    path('skapa-konto/', views.RegisterView.as_view(), name='register'),
    path("compare-candidates/", views.compare_candidates_page, name="compare_candidates"),
    path("compare-candidates/api/", views.compare_candidates_api, name="compare_candidates_api"),
    path('testtolkare/upload/', views.upload_test_result, name='upload_test_result'),
    path('testtolkare/result/<int:pk>/', views.test_result_detail, name='test_result_detail'),
    path("testtolkare/api/stream/<int:pk>/", views.testtolkare_stream_response, name="testtolkare_stream"),
]