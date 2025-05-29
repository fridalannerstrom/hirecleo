from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse

# === Jobb ===
class Job(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
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

# === Kandidat ===
class Candidate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="candidates")
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    cv_text = models.TextField(blank=True, null=True)
    interview_notes = models.TextField(blank=True, null=True)
    test_results = models.TextField(blank=True, null=True)
    
    jobs = models.ManyToManyField(Job, related_name="candidates", blank=True)
    
    slug = models.SlugField(max_length=200, unique=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    top_skills = models.JSONField(blank=True, null=True, default=list)
    uploaded_pdf = models.FileField(upload_to='candidate_pdfs/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

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

# === Profil ===
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='profile_pics/', default='default.png')

    def __str__(self):
        return f'{self.user.username} Profile'

# === Cleo-dokument (för embedding/AI) ===
class CleoDocument(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    embedding_id = models.CharField(max_length=255, blank=True, null=True)  # Pinecone ID
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# === Chatfunktioner ===
class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} – {self.title} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=[('user', 'User'), ('cleo', 'Cleo')])
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.timestamp.strftime('%H:%M')} {self.sender}: {self.message[:30]}"


# === Jobbannonser ===
class JobAd(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
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