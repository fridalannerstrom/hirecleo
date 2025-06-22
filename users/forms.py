from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class TestChatMessageForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("email",)