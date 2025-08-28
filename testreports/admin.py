from django.contrib import admin
from .models import TestReport

@admin.register(TestReport)
class TestReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'uploaded_file', 'created_on')
    list_filter = ('created_on',)
    search_fields = ('uploaded_file', 'user__email')