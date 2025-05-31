from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from jobs.models import Job, JobAd
from openai import OpenAI
from candidates.models import Candidate
from core.pdf_utils import read_pdf_text
from core.openai_utils import (
    extract_candidate_data_with_openai,
    extract_job_data_with_openai,
    clean_cv_text,
    reformat_cv_text_with_openai,
    parse_json_result
)

import uuid
import re
import json
from bs4 import BeautifulSoup

client = OpenAI()

@login_required
def create_jobad(request):
    jobs = Job.objects.filter(user=request.user)

    if request.method == 'POST':
        content = request.POST.get('content')
        job_id = request.POST.get('job') or request.POST.get('job_id')
        job = None

        if job_id and job_id.strip() and job_id.strip().isdigit():
            job = get_object_or_404(Job, id=job_id, user=request.user)
        else:
            soup = BeautifulSoup(content or "", "html.parser")
            plain_text = soup.get_text()
            try:
                ai_summary_prompt = f"""
Här är en jobbannons. Extrahera följande information:
- Titel
- Företagsnamn
- Plats
- Anställningstyp

Returnera **endast** ett JSON-objekt i detta format (utan inledande text):
{{
"title": "...",
"company": "...",
"location": "...",
"employment_type": "..."
}}

Jobbannons:
\"\"\"{plain_text[:2000]}\"\"\"
"""
                ai_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Du är en rekryteringsexpert."},
                        {"role": "user", "content": ai_summary_prompt}
                    ]
                )
                raw_content = ai_response.choices[0].message.content
                json_match = re.search(r'\{.*?\}', raw_content, re.DOTALL)
                if json_match:
                    extracted = json.loads(json_match.group(0))
                else:
                    raise ValueError("Kunde inte hitta JSON i GPT-svaret")
            except Exception:
                extracted = {
                    "title": "Jobbannons",
                    "company": "Ej angivet",
                    "location": "Ej angivet",
                    "employment_type": "Ej angivet"
                }

            job = Job.objects.create(
                user=request.user,
                title=extracted["title"],
                company=extracted["company"],
                location=extracted["location"],
                employment_type=extracted["employment_type"],
                description=plain_text[:1000],
                slug=slugify(f"{extracted['title']}-{uuid.uuid4().hex[:6]}")
            )

        JobAd.objects.create(
            user=request.user,
            job=job,
            title=job.title,
            content=content,
            is_draft=True
        )

        return redirect('job_detail', slug=job.slug)

    return render(request, 'generator/jobad-create.html', {'jobs': jobs})

@csrf_exempt
@login_required
def generate_jobad_api(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Endast POST tillåtet."}, status=405)

    prompt = request.POST.get("prompt", "").strip()
    job_id = request.POST.get("job_id")
    uploaded_file = request.FILES.get("job_file")

    # 1. Om ett jobb valts
    if job_id and job_id.strip().isdigit():
        try:
            job = get_object_or_404(Job, id=job_id, user=request.user)
            prompt = f"""
Skapa en jobbannons baserad på detta jobb:
Titel: {job.title}
Företag: {job.company}
Plats: {job.location}
Anställning: {job.employment_type}
Beskrivning: {job.description}
"""
        except Exception as e:
            return JsonResponse({"error": f"Kunde inte hämta jobbet: {str(e)}"}, status=400)

    # 2. Om fil laddats upp
    elif uploaded_file:
        try:
            if uploaded_file.name.endswith(".pdf"):
                from PyPDF2 import PdfReader
                pdf = PdfReader(uploaded_file)
                text = ''.join(page.extract_text() for page in pdf.pages if page.extract_text())
            else:
                text = uploaded_file.read().decode("utf-8", errors="ignore")

            prompt = f"Skapa en jobbannons baserat på denna text:\n{text}"
        except Exception as e:
            return JsonResponse({"error": f"Fel vid filhantering: {str(e)}"}, status=400)

    # 3. Om prompt fortfarande saknas
    if not prompt:
        return JsonResponse({"error": "Ingen input hittades."}, status=400)

    # 4. Skicka till OpenAI
    ai_prompt = f"""
Du är en expert på att skriva jobbannonser. Skapa en färdigformaterad annons i ren HTML (använd <h2>, <ul>, <p>, <strong>, etc).
Använd rubriker för sektioner, punktlistor och korta stycken.

Här är input:

\"\"\"{prompt}\"\"\"
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Du är en expert på att skriva jobbannonser."},
                {"role": "user", "content": ai_prompt}
            ]
        )
        content = response.choices[0].message.content.strip()
        content = re.sub(r"```html|```", "", content).strip()

        return JsonResponse({"content": content, "suggested_title": "Jobbannons"})
    except Exception as e:
        return JsonResponse({"error": f"OpenAI-fel: {str(e)}"}, status=500)

@login_required
def jobad_detail(request, pk):
    ad = get_object_or_404(JobAd, pk=pk, user=request.user)
    return render(request, 'generator/jobads/jobad_detail.html', {'ad': ad})
