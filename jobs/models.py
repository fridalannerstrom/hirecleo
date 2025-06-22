from django.db import models
from django.conf import settings
from django.urls import reverse

class Job(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    employment_type = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    uploaded_pdf = models.FileField(upload_to='job_pdfs/', blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return f"{self.title} @ {self.company}"

    class Meta:
        ordering = ['-created_on']

    def get_absolute_url(self):
        return reverse('job_detail', args=[str(self.slug)])


class JobAd(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255)
    content = models.TextField()  # AI-genererad + ev. redigerad text
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    is_draft = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} ({'Utkast' if self.is_draft else 'Publicerad'})"

    class Meta:
        ordering = ['-created_on']

    def get_absolute_url(self):
        return reverse('jobad_detail', args=[str(self.id)])