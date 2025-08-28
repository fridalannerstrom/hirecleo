from django.db import models
from django.conf import settings
from jobs.models import Job

class TestReport(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_file = models.FileField(upload_to='test_reports/')
    extracted_text = models.TextField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    linked_job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Report #{self.id} – {self.uploaded_file.name}"

    class Meta:
        ordering = ['-created_on']