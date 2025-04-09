from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Job(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="jobs")
    title = models.CharField(max_length=50)
    description = models.TextField()
    slug = models.SlugField(max_length=200, unique=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Candidate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="candidates")
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    linkedin_url = models.URLField(blank=True)
    cv_text = models.TextField(blank=True)
    interview_notes = models.TextField(blank=True)
    test_results = models.TextField(blank=True)
    jobs = models.ManyToManyField(Job, related_name="candidates")
    slug = models.SlugField(max_length=200, unique=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='profile_pics/', default='default.png')

    def __str__(self):
        return f'{self.user.username} Profile'
