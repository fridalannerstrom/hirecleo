from django.contrib import admin
from .models import Candidate, Job, Profile

# Register your models here.
admin.site.register(Candidate)
admin.site.register(Job)
admin.site.register(Profile)