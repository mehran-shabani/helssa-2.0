"""
URL patterns for the chatbot app.
"""
from django.urls import path

from chatbot.views import ChatStreamView, index

app_name = "chatbot"

urlpatterns = [
    path("", index, name="index"),
    path("api/chat/", ChatStreamView.as_view(), name="chat_stream"),
]
