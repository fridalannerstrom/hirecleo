import json
import re
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI
from jobs.models import Job
from candidates.models import Candidate

client = OpenAI()

# 🌐 Sida: HTML-vy för att visa kandidatjämförelseformuläret
@login_required
def compare_candidates_page(request):
    jobs = Job.objects.filter(user=request.user)
    candidates = Candidate.objects.filter(user=request.user)
    return render(request, "comparator/compare-candidates.html", {
        "jobs": jobs,
        "candidates": candidates
    })


# 🤖 API: GPT-baserad jämförelse med score + kommentar
@csrf_exempt
@login_required
def compare_candidates_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Endast POST tillåtet"}, status=405)

    try:
        data = json.loads(request.body)
        job_id = data.get("job_id")
        candidate_ids = data.get("candidate_ids", [])

        if not job_id or not candidate_ids:
            return JsonResponse({"error": "job_id och candidate_ids krävs"}, status=400)

        job = get_object_or_404(Job, id=job_id, user=request.user)
        candidates = Candidate.objects.filter(id__in=candidate_ids, user=request.user)

        job_text = f"""Titel: {job.title}
Företag: {job.company}
Plats: {job.location}
Anställningsform: {job.employment_type}
Beskrivning: {job.description}"""

        results = []

        for candidate in candidates:
            summary = f"""
Namn: {candidate.first_name} {candidate.last_name}
E-post: {candidate.email or '-'}
LinkedIn: {candidate.linkedin_url or '-'}
CV-text: {candidate.cv_text or '-'}
Intervjunoter: {candidate.interview_notes or '-'}
Testrapporter: {candidate.test_results or '-'}
"""

            prompt = f"""
Du är en rekryteringsexpert. Baserat på följande jobbannons och information om kandidaten, ge:

1. En **matchningsscore mellan 0 och 100**
2. En **kort kommentar** som förklarar varför kandidaten är (eller inte är) en bra match.

Formatet på svaret ska vara exakt så här:
Score: [siffra]
Kommentar: [text]

JOBB:
{job_text}

KANDIDAT:
{summary}
"""

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Du är en rekryteringsexpert."},
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.choices[0].message.content.strip()

            # Enkel parsing
            score = None
            comment = None
            for line in content.splitlines():
                if line.lower().startswith("score:"):
                    score = int(''.join(filter(str.isdigit, line)))
                elif line.lower().startswith("kommentar:"):
                    comment = line.split(":", 1)[-1].strip()

            results.append({
                "candidate_name": f"{candidate.first_name} {candidate.last_name}",
                "score": score if score is not None else 0,
                "summary": comment or "Kommentar saknas"
            })

        return JsonResponse({"results": results})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)