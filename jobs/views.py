from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
import uuid
import re
import json
from bs4 import BeautifulSoup
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI
from jobs.models import Job, JobAd
from core.views import read_pdf_text
from core.views import (
    extract_candidate_data_with_openai,
    extract_job_data_with_openai,
    clean_cv_text,
    reformat_cv_text_with_openai,
    parse_json_result
)
from django.urls import reverse

client = OpenAI()


@login_required
def your_jobs(request):
    jobs = Job.objects.filter(user=request.user).order_by('-created_on')
    return render(request, 'jobs/your-jobs.html', {'jobs': jobs})


@login_required
def add_jobs_manually(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        company = request.POST.get('company')
        location = request.POST.get('location')
        employment_type = request.POST.get('employment_type')
        description = request.POST.get('description')

        # Generera unik slug
        base_slug = slugify(title)
        slug = base_slug
        counter = 1
        while Job.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{uuid.uuid4().hex[:4]}"
            counter += 1

        Job.objects.create(
            user=request.user,
            title=title,
            company=company,
            location=location,
            employment_type=employment_type,
            description=description,
            slug=slug
        )

        return redirect('your_jobs')

    return render(request, 'jobs/add-jobs-manually.html')


@login_required
def add_jobs_pdf(request):
    if request.method == 'POST':
        files = request.FILES.getlist('uploaded_pdf')

        for pdf_file in files:
            print(f"📄 Behandlar fil: {pdf_file.name}")
            job = Job(uploaded_pdf=pdf_file, user=request.user)

            try:
                raw_text = read_pdf_text(pdf_file)
                print("✅ Text extraherad")

                result = extract_job_data_with_openai(raw_text)

                # Om resultatet är en sträng, försök omvandla till dict
                if isinstance(result, str):
                    cleaned = re.sub(r"```json|```", "", result).strip()
                    data = json.loads(cleaned)
                elif isinstance(result, dict):
                    data = result
                else:
                    raise ValueError("❌ Oväntat format från OpenAI")

                # Fyll i jobbfält
                job.title = data.get('Titel', '')
                job.company = data.get('Företag', '')
                job.location = data.get('Plats', '')
                job.employment_type = data.get('Anställningsform', '')
                job.description = data.get('Beskrivning', '')

                if not job.title:
                    print("⚠️ Titel saknas – hoppar över sparning.")
                    continue

                job.slug = slugify(f"{job.title}-{uuid.uuid4().hex[:6]}")
                job.save()
                print(f"✅ Job sparat: {job.title}")

            except Exception as e:
                print(f"❌ Error parsing job from {pdf_file.name}: {e}")

        return redirect('your_jobs')

    jobs = Job.objects.filter(user=request.user).order_by('-created_on')
    return render(request, 'jobs/add-jobs-pdf.html', {'jobs': jobs})


@login_required
def job_detail(request, slug):
    job = get_object_or_404(Job, slug=slug, user=request.user)
    return render(request, 'jobs/your-jobs-detail.html', {'job': job})


@login_required
def delete_job(request, slug):
    job = get_object_or_404(Job, slug=slug, user=request.user)
    if request.method == 'POST':
        job.delete()
        return redirect('your_jobs')
    return redirect('your_jobs')  # fallback if GET


@login_required
def edit_job(request, slug):
    job = get_object_or_404(Job, slug=slug, user=request.user)

    if request.method == 'POST':
        job.title = request.POST.get('title')
        job.company = request.POST.get('company')
        job.location = request.POST.get('location')
        job.employment_type = request.POST.get('employment_type')
        job.description = request.POST.get('description')
        job.save()
        return redirect('your_jobs')

    return render(request, 'jobs/your-jobs-edit.html', {'job': job})

@login_required
def jobad_detail(request, pk):
    ad = get_object_or_404(JobAd, pk=pk, user=request.user)
    return render(request, 'jobads/jobad_detail.html', {'ad': ad})


def extract_job_data_with_openai(text):
    prompt = f"""
Här är en jobbannons i textformat:

\"\"\"{text}\"\"\"

Extrahera följande som JSON:
- Titel
- Företag
- Plats
- Anställningsform
- Beskrivning (kort, renskriven version)

Returnera bara JSON, utan kommentarer.
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Du är en expert på att tolka jobbannonser."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=600
    )
    return response.choices[0].message.content

@csrf_exempt
@login_required
def save_interview_questions(request, job_id):
    if request.method == "POST":
        job = get_object_or_404(Job, id=job_id, user=request.user)
        content = request.POST.get("questions", "").strip()

        if content:
            job.interview_questions = content
            job.save()
            return JsonResponse({
                "success": True,
                "redirect_url": reverse("job_detail", args=[job.id])
            })

        return JsonResponse({"success": False, "error": "Inget innehåll"})
    
    return JsonResponse({"error": "Invalid request"}, status=400)