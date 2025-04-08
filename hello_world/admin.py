from django.contrib import admin
from .models import Candidate, Job

# Register your models here.
admin.site.register(Candidate)
admin.site.register(Job)