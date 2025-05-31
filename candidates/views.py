from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Candidate
from testanalyzer.models import TestResult  # Om du även hanterar testresultat här
import uuid
import logging
import markdown
import json

from core.pdf_utils import read_pdf_text
from core.openai_utils import (
    extract_candidate_data_with_openai,
    extract_job_data_with_openai,
    clean_cv_text,
    reformat_cv_text_with_openai,
    parse_json_result
)

logger = logging.getLogger(__name__)


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

        base_slug = slugify(f"{first_name}-{last_name}")
        slug = base_slug
        counter = 1
        while Candidate.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

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

    return render(request, 'candidates/add-candidates-manually.html')


@login_required
def add_candidates_pdf(request):
    if request.method == 'POST':
        files = request.FILES.getlist('uploaded_pdf')

        for pdf_file in files:
            candidate = Candidate(uploaded_pdf=pdf_file, user=request.user)

            # 📄 Extrahera text från PDF
            raw_text = read_pdf_text(pdf_file)
            candidate.cv_text = raw_text

            try:
                # 🧠 Extrahera kandidatdata via GPT (JSON som dict)
                data = extract_candidate_data_with_openai(raw_text)
                print("✅ Parsed JSON:", data)

                # 🧍 Fyll i kandidatens fält
                candidate.first_name = (data.get('Förnamn') or '').strip()
                candidate.last_name = (data.get('Efternamn') or '').strip()
                candidate.email = (data.get('E-postadress') or '').strip()
                candidate.phone_number = (data.get('Telefonnummer') or '').strip()
                candidate.linkedin_url = (data.get('LinkedIn-länk') or '').strip()
                candidate.top_skills = data.get('Top Skills') or []

                # 🧼 Rensa och ✨ formatera CV
                candidate.cv_text = clean_cv_text(
                    raw_text,
                    phone=candidate.phone_number,
                    email=candidate.email,
                    linkedin=candidate.linkedin_url,
                )
                candidate.cv_text = reformat_cv_text_with_openai(candidate.cv_text)

                # 🐌 Generera unik slug
                base_slug = f"{candidate.first_name}-{candidate.last_name}".lower().replace(" ", "-")
                slug = base_slug
                counter = 1
                while Candidate.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                candidate.slug = slug

            except Exception as e:
                logger.warning("❌ Fel vid AI-tolkning: %s", str(e))
                print("❌ Exception i kandidatparsing:", e)

            print("📄 Extraherad text från PDF:\n", candidate.cv_text[:500])
            candidate.save()

        return redirect('add_candidates_pdf')

    candidates = Candidate.objects.filter(user=request.user).order_by('-created_on')
    return render(request, 'candidates/add-candidates-pdf.html', {'candidates': candidates})


@login_required
def candidate_detail(request, slug):
    candidate = get_object_or_404(Candidate, slug=slug, user=request.user)
    cv_html = markdown.markdown(candidate.cv_text)
    return render(request, 'candidates/your-candidates-profile.html', {
        'candidate': candidate,
        'cv_html': cv_html
    })


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

    return render(request, 'candidates/your-candidates-edit.html', {'candidate': candidate})


@login_required
def delete_candidate(request, slug):
    candidate = get_object_or_404(Candidate, slug=slug, user=request.user)
    candidate.delete()
    return redirect('your_candidates')


@login_required
def your_candidates(request):
    candidates = Candidate.objects.filter(user=request.user).order_by('-created_on')
    return render(request, 'candidates/your-candidates.html', {'candidates': candidates})


@csrf_exempt
@login_required
def save_test_to_candidate(request, slug):
    if request.method == "POST":
        candidate = get_object_or_404(Candidate, slug=slug, user=request.user)
        test_summary = request.POST.get("test_summary")

        if not test_summary:
            return JsonResponse({"error": "Missing test summary"}, status=400)

        candidate.test_results = (candidate.test_results or "") + f"\n\n{test_summary}"
        candidate.save()

        return JsonResponse({"success": True})

    return JsonResponse({"error": "Invalid method"}, status=405)


@csrf_exempt
@login_required
def create_new_candidate_from_test(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        test_summary = request.POST.get("test_summary")

        if not all([first_name, last_name, test_summary]):
            return JsonResponse({"error": "Missing required fields"}, status=400)

        slug_base = slugify(f"{first_name}-{last_name}")
        slug = slug_base
        counter = 1
        while Candidate.objects.filter(slug=slug).exists():
            slug = f"{slug_base}-{counter}"
            counter += 1

        new_candidate = Candidate.objects.create(
            user=request.user,
            first_name=first_name,
            last_name=last_name,
            test_results=test_summary,
            slug=slug
        )

        return JsonResponse({
            "success": True,
            "redirect_url": f"/candidate/{slug}/"
        })

    return JsonResponse({"error": "Invalid method"}, status=405)


@csrf_exempt
@login_required
def find_matching_candidate(request):
    data = json.loads(request.body)
    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()

    match = Candidate.objects.filter(first_name__iexact=first_name, last_name__iexact=last_name, user=request.user).first()
    if match:
        return JsonResponse({"found": True, "full_name": f"{match.first_name} {match.last_name}"})
    else:
        return JsonResponse({"found": False})


@csrf_exempt
@login_required
def save_summary_to_existing(request):
    data = json.loads(request.body)
    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()
    summary = data.get("summary", "")

    candidate = Candidate.objects.filter(first_name__iexact=first_name, last_name__iexact=last_name, user=request.user).first()
    if candidate:
        candidate.test_results = (candidate.test_results or "") + f"\n\n{summary}"
        candidate.save()
        return JsonResponse({"status": "saved"})
    return JsonResponse({"error": "Candidate not found"}, status=404)


@csrf_exempt
@login_required
def save_summary_as_new_candidate(request):
    data = json.loads(request.body)
    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()
    summary = data.get("summary", "")

    candidate = Candidate.objects.create(
        user=request.user,
        first_name=first_name,
        last_name=last_name,
        test_results=summary
    )
    return JsonResponse({"redirect_url": candidate.get_absolute_url()})