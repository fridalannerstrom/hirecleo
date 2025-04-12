from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import ProfileImageForm, CandidatePDFUploadForm
from .models import Candidate, Profile
from django.utils.text import slugify
import uuid

# Create your views here.
def dashboard(request):
    return render(request, 'dashboard.html')

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

@login_required
def add_candidates_manually(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        linkedin_url = request.POST.get('linkedin_url')
        top_skills_raw = request.POST.get('top_skills', '')
        top_skills = [skill.strip() for skill in top_skills_raw.split(',') if skill.strip()]
        cv_text = request.POST.get('cv_text')
        interview_notes = request.POST.get('interview_notes')
        test_results = request.POST.get('test_results')

        # Generera unik slug
        base_slug = slugify(f"{first_name}-{last_name}")
        slug = base_slug
        counter = 1
        while Candidate.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        # Skapa kandidat
        Candidate.objects.create(
            user=request.user,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            linkedin_url=linkedin_url,
            top_skills=top_skills,
            cv_text=cv_text,
            interview_notes=interview_notes,
            test_results=test_results,
            slug=slug,
        )

        return redirect('your_candidates') 

    return render(request, 'add-candidates-manually.html')

@login_required
def add_candidates_pdf(request):
    return render(request, 'add-candidates-pdf.html')

@login_required
def your_candidates(request):
    candidates = Candidate.objects.filter(user=request.user).order_by('-created_on')
    return render(request, 'your-candidates.html', {'candidates': candidates})

@login_required
def your_jobs(request):
    return render(request, 'your-jobs.html')

@login_required
def add_jobs_manually(request):
    return render(request, 'add-jobs-manually.html')

@login_required
def add_jobs_pdf(request):
    return render(request, 'add-jobs-pdf.html')

@login_required
def chat(request):
    return render(request, 'chat.html')

@login_required
def candidate_detail(request, slug):
    candidate = get_object_or_404(Candidate, slug=slug, user=request.user)
    return render(request, 'your-candidates-profile.html', {'candidate': candidate})

@login_required
def edit_candidate(request, slug):
    candidate = get_object_or_404(Candidate, slug=slug, user=request.user)

    if request.method == 'POST':
        candidate.first_name = request.POST.get('first_name')
        candidate.last_name = request.POST.get('last_name')
        candidate.email = request.POST.get('email')
        candidate.phone_number = request.POST.get('phone_number')
        candidate.linkedin_url = request.POST.get('linkedin_url')
        candidate.cv_text = request.POST.get('cv_text')
        candidate.interview_notes = request.POST.get('interview_notes')
        candidate.test_results = request.POST.get('test_results')

        top_skills_raw = request.POST.get('top_skills', '')
        candidate.top_skills = [s.strip() for s in top_skills_raw.split(',') if s.strip()]

        candidate.save()
        return redirect('candidate_detail', slug=candidate.slug)

    return render(request, 'your-candidates-edit.html', {'candidate': candidate})

@login_required
def delete_candidate(request, slug):
    candidate = get_object_or_404(Candidate, slug=slug, user=request.user)
    candidate.delete()
    return redirect('your_candidates')

def add_candidates_pdf(request):
    if request.method == 'POST':
        form = CandidatePDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            candidate = form.save(commit=False)

            # Sätt nödvändiga fält med placeholder-värden om de saknas
            candidate.first_name = "Unnamed"
            candidate.last_name = "Candidate"
            candidate.email = "no@email.com"
            candidate.phone_number = ""
            candidate.user = request.user

            # Lägg till en slug så inte reverse failar
            filename = request.FILES['uploaded_pdf'].name
            slug_base = slugify(filename.replace('.pdf', ''))
            candidate.slug = f"{slug_base}-{uuid.uuid4().hex[:8]}"

            candidate.save()
            return redirect('add_candidates_pdf')  # återladdar sidan efter uppladdning
    else:
        form = CandidatePDFUploadForm()

    # Justera sorteringsfält till 'created_on' om 'uploaded_at' inte finns
    candidates = Candidate.objects.filter(uploaded_pdf__isnull=False).order_by('-created_on')

    return render(request, 'add-candidates-pdf.html', {
        'form': form,
        'candidates': candidates
    })