from django import forms
from .models import Profile  # Du skapar Profile-modellen i models.py

class ProfileImageForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image']