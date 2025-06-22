from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
from jobs.models import Job  # Du behöver importera Job här eftersom det är en relation

class Candidate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="candidates")
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    cv_text = models.TextField(blank=True, null=True)
    interview_notes = models.TextField(blank=True, null=True)
    test_results = models.TextField(blank=True, null=True)
    title = models.CharField(max_length=100, blank=True, null=True)
    
    jobs = models.ManyToManyField(Job, related_name="candidates", blank=True)
    
    slug = models.SlugField(max_length=200, unique=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    top_skills = models.JSONField(blank=True, null=True, default=list)
    uploaded_pdf = models.FileField(upload_to='candidate_pdfs/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_absolute_url(self):
        return reverse("candidate_detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.first_name}-{self.last_name}")
            unique_slug = base_slug
            counter = 1
            while Candidate.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_on']
