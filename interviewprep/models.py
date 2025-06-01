from django.db import models
from candidates.models import Candidate
from jobs.models import Job

class InterviewPrep(models.Model):
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True)
    candidate = models.ForeignKey(Candidate, on_delete=models.SET_NULL, null=True, blank=True)
    generated_questions = models.TextField(blank=True, null=True)
    ai_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)