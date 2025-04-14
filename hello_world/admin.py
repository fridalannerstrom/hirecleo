from django.contrib import admin
from .models import Candidate, Job, Profile, CleoDocument

# Register your models here.
admin.site.register(Candidate)
admin.site.register(Job)
admin.site.register(Profile)

@admin.register(CleoDocument)
class CleoDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at", "embedding_id")