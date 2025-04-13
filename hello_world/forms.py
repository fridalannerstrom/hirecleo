from django import forms
from .models import Profile, Candidate

class ProfileImageForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image']
