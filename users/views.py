import os
import fitz  # PyMuPDF
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
import uuid
from openai import OpenAI
from PyPDF2 import PdfReader
if os.path.exists("env.py"):
    import env
import re
import markdown
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import StreamingHttpResponse, JsonResponse, HttpResponseBadRequest
from asgiref.sync import sync_to_async
from pinecone import Pinecone
from django.contrib.auth.forms import UserCreationForm
from django.views import View
from django.shortcuts import render, redirect
from bs4 import BeautifulSoup
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import TestResult
from openai import OpenAI
from PyPDF2 import PdfReader
from .forms import TestChatMessageForm  # valfritt om du vill ha ett formulärobjekt
import uuid
from candidates.models import Candidate
from jobs.models import Job, JobAd
from .forms import CustomUserCreationForm


def dashboard(request):
    return render(request, 'dashboard.html')


class RegisterView(View):
    def get(self, request):
        form = CustomUserCreationForm()
        return render(request, 'users/auth-register-basic.html', {'form': form})

    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # logga in direkt efter skapande
            return redirect('dashboard')
        return render(request, 'users/auth-register-basic.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'users/auth-login-basic.html', {'error': 'Fel e-post eller lösenord'})
    return render(request, 'users/auth-login-basic.html')

def logout_view(request):
    logout(request)
    return redirect('login')  # Skicka användaren till inloggningssidan efter logout

@login_required
def dashboard_view(request):
    return render(request, 'dashboard.html')

