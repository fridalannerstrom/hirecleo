from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ProfileImageForm

# Create your views here.
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

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')  # eller 'email' om du använder det
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')  # namnet på din url
        else:
            return render(request, 'auth-login-basic.html', {'error': 'Invalid credentials'})
    return render(request, 'auth-login-basic.html')

def logout_view(request):
    logout(request)
    return redirect('login')  # Skicka användaren till inloggningssidan efter logout

@login_required
def dashboard_view(request):
    return render(request, 'dashboard.html')

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileImageForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
    else:
        form = ProfileImageForm(instance=request.user.profile)

    return render(request, 'profile.html', {'form': form})

@login_required
def dashboard_view(request):
    # Om profilen inte finns, skapa en
    Profile.objects.get_or_create(user=request.user)
    return render(request, 'dashboard.html')


@login_required
def account_profile(request):
    user = request.user
    profile = user.profile
    form = ProfileImageForm(instance=profile)

    if request.method == 'POST':
        form = ProfileImageForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()

        # Kolla om användarfälten finns innan vi sparar dem
        if 'first_name' in request.POST:
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.email = request.POST.get('email', user.email)
            user.save()

        return redirect('account_profile')

    return render(request, 'account-profile.html', {
        'form': form
    })