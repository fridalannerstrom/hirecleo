from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
from candidates.models import Candidate
from jobs.models import Job, JobAd
from testanalyzer.models import TestResult

# === Chatfunktioner ===
class ChatSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    test_result = models.ForeignKey(TestResult, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} – {self.title} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=[('user', 'User'), ('cleo', 'Cleo')])
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.timestamp.strftime('%H:%M')} {self.sender}: {self.message[:30]}"

# === Cleo-dokument (för embedding/AI) ===
class CleoDocument(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    embedding_id = models.CharField(max_length=255, blank=True, null=True)  # Pinecone ID
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
