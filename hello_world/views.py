from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def index(request):
    return HttpResponse("Hello, world! This is my first Django app.")   

def dashboard(request):
    return render(request, 'dashboard.html')

def candidates(request):
    return render(request, 'candidates.html')

def upload_candidates(request):
    return render(request, 'upload_candidates.html')

def jobs(request):
    return render(request, 'jobs.html')

def upload_jobs(request):
    return render(request, 'upload_jobs.html')

def jobad(request):
    return render(request, 'jobad.html')