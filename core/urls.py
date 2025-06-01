from django.urls import path
from core import views
from users import views as user_views

urlpatterns = [
    path('', user_views.dashboard, name='dashboard'),
    path('chat-response/', views.chat_response, name='chat_response'),
    path('start-session/', views.start_new_session, name='start_session'),
    path('save-message/', views.save_message, name='save_message'),
]