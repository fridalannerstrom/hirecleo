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

from core.views import read_pdf_text
from core.views import (
    extract_candidate_data_with_openai,
    extract_job_data_with_openai,
    clean_cv_text,
    reformat_cv_text_with_openai,
    parse_json_result
)

from core.utils import generate_unique_slug

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

        slug = generate_unique_slug(Candidate, [first_name, last_name])

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
            pdf_file.seek(0) 
            
            candidate = Candidate(uploaded_pdf=pdf_file, user=request.user)

            # 📄 Extrahera text från PDF
            raw_text = read_pdf_text(pdf_file)
            candidate.cv_text = raw_text

            try:
                # 🧠 Extrahera kandidatdata via GPT (JSON som dict)
                try:
                    print("🧠 Skickar till extract_candidate_data_with_openai...")
                    data = extract_candidate_data_with_openai(raw_text)
                    print("✅ AI-resultat mottaget:", data)
                except Exception as e:
                    print("❌ Exception i kandidatparsing:", e)
                    data = {}  # sätt fallback så resten kan fortsätta
                print("✅ Parsed JSON:", data)

                # 🧍 Fyll i kandidatens fält
                candidate.first_name = (data.get('Förnamn') or '').strip()
                candidate.last_name = (data.get('Efternamn') or '').strip()
                candidate.email = (data.get('E-postadress') or '').strip()
                candidate.phone_number = (data.get('Telefonnummer') or '').strip()
                candidate.linkedin_url = (data.get('LinkedIn-länk') or '').strip()
                candidate.top_skills = data.get('Top Skills') or []
                candidate.title = (data.get('Titel') or '').strip()

                # 🧼 Rensa och ✨ formatera CV
                candidate.cv_text = clean_cv_text(
                    raw_text,
                    phone=candidate.phone_number,
                    email=candidate.email,
                    linkedin=candidate.linkedin_url,
                )
                candidate.cv_text = reformat_cv_text_with_openai(candidate.cv_text)

                candidate.slug = generate_unique_slug(Candidate, [candidate.first_name, candidate.last_name])

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
    test_html = markdown.markdown(candidate.test_results or "")
    return render(request, 'candidates/your-candidates-profile.html', {
        'candidate': candidate,
        'cv_html': cv_html,
        'test_html': test_html
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

        slug = generate_unique_slug(Candidate, [first_name, last_name])

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

@login_required
def upload_test_result(request, slug):
    candidate = get_object_or_404(Candidate, slug=slug, user=request.user)

    if request.method == "POST" and request.FILES.get("test_file"):
        test_file = request.FILES["test_file"]
        TestResult.objects.create(
            user=request.user,  # 👈 detta saknades
            candidate=candidate,
            uploaded_file=test_file
)
    
    return redirect("candidate_detail", slug=slug)

from core.views import read_pdf_text, normalize_pdf_text, client  # se till att OpenAI är importerat

@login_required
def summarize_test_results(request, slug):
    candidate = get_object_or_404(Candidate, slug=slug, user=request.user)

    # Läs all text från testresultat
    texts = []
    for result in candidate.testresult_set.all():
        if not result.extracted_text:
            raw = read_pdf_text(result.uploaded_file)
            result.extracted_text = normalize_pdf_text(raw)
            result.save()
        texts.append(result.extracted_text)

    full_text = "\n\n".join(texts).strip()

    if not full_text:
        return JsonResponse({"error": "Inget innehåll hittades i testfilerna."}, status=400)

    # Skicka till GPT
    prompt = f"""
Här är olika testresultat för en kandidat:

\"\"\"{full_text}\"\"\"

Analysera dem och skriv en sammanfattning av:
- Kandidatens styrkor
- Eventuella utvecklingsområden
- Vad testresultaten visar om arbetsstil, förmågor och lämplighet
- Om möjligt, ge ett helhetsintryck med tydliga rubriker.

Skriv professionellt på svenska.
"""

    print("📤 Prompt till GPT:\n", prompt[:10000])

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Du är en expert på testanalys inom rekrytering."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000
    )

    summary = response.choices[0].message.content.strip()
    candidate.test_results = summary
    candidate.save()

    return redirect("candidate_detail", slug=slug)

@login_required
def delete_test_result(request, id):
    result = get_object_or_404(TestResult, id=id, user=request.user)

    slug = result.candidate.slug if result.candidate else None
    result.uploaded_file.delete(save=False)  # Ta bort filen från media
    result.delete()

    if slug:
        return redirect('candidate_detail', slug=slug)
    return redirect('your_candidates')