from django.urls import path
from . import views

urlpatterns = [
    path("chat-response/", views.chat_response, name="chat_response"),
    path("start-session/", views.start_new_session, name="start_session"),
    path("save-message/", views.save_message, name="save_message"),
]