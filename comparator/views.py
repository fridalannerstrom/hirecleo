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
Testresultat: {candidate.test_results or '-'}
"""

            prompt = f"""
            Du är en rekryteringsexpert. Baserat på följande jobbannons och kandidatinfo, ge:

            1. En kort sammanfattning av kandidatens styrkor och utvecklingsområden (max 3 meningar)
            2. En kort sammanfattning av testresultatet (max 2 meningar). Om testresultat inte finns, skriv "Inga testresultat tillgängliga".
            3. En rekommendation: "🟢 Rekommenderas" eller "🟠 Rekommenderas inte" för jobbet

            Returnera som JSON med nycklarna:
            "Sammanfattning", "Testresultat", "Rekommendation"

            JOBB:
            {job_text}

            KANDIDAT:
            {summary}
            """

            print("📤 PROMPT TILL GPT:\n", prompt)

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Du är en rekryteringsexpert."},
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.choices[0].message.content.strip()
            print("📥 SVAR FRÅN GPT:\n", content)

            try:
                parsed = json.loads(re.sub(r"```json|```", "", content).strip())
            except json.JSONDecodeError:
                parsed = {}

            results.append({
                "candidate_name": f"{candidate.first_name} {candidate.last_name}",
                "title": candidate.title or "Ingen titel",
                "top_skills": candidate.top_skills or [],
                "test_summary": parsed.get("Testresultat", "–"),
                "summary": parsed.get("Sammanfattning", "–"),
                "recommendation": parsed.get("Rekommendation", "–"),
            })

        return JsonResponse({"results": results})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)