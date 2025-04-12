from django import forms
from .models import Profile, Candidate

class ProfileImageForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image']

class CandidatePDFUploadForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ['uploaded_pdf']