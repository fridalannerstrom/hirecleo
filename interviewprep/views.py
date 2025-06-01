from django.shortcuts import render, redirect
from .models import InterviewPrep
from jobs.models import Job
from candidates.models import Candidate
from core.views import read_pdf_text, normalize_pdf_text

def prepare_interview(request):
    if request.method == "POST":
        job_id = request.POST.get("job_id")
        candidate_id = request.POST.get("candidate_id")
        free_text = request.POST.get("prompt")
        job_file = request.FILES.get("job_file")  # 👈 uppladdad PDF

        job = Job.objects.filter(id=job_id).first() if job_id else None
        candidate = Candidate.objects.filter(id=candidate_id).first() if candidate_id else None

        # ⬇️ Kombinera alla möjliga jobbkällor
        job_text_parts = []

        if free_text:
            job_text_parts.append(f"Fritext från användaren:\n{free_text.strip()}")

        if job and job.description:
            job_text_parts.append(f"Jobbeskrivning från databasen:\n{job.description.strip()}")

        if job_file:
            pdf_text = read_pdf_text(job_file)
            cleaned_text = normalize_pdf_text(pdf_text)
            job_text_parts.append(f"Text extraherad från PDF:\n{cleaned_text}")

        job_description = "\n\n".join(job_text_parts).strip()

        print("📄 Kombinerad jobbeskrivning som skickas till OpenAI:\n", job_description)

        questions, notes = generate_interview_questions(job_description, candidate)

        InterviewPrep.objects.create(
            job=job,
            candidate=candidate,
            generated_questions=questions,
            ai_notes=notes
        )

        return render(request, 'interviewprep/result.html', {
            'result': questions,
            'candidate': candidate,
            'candidate_summary': notes
        })

    return render(request, 'interviewprep/form.html', {
        'jobs': Job.objects.all(),
        'candidates': Candidate.objects.all()
    })

from openai import OpenAI
client = OpenAI()

def generate_interview_questions(job_text, candidate=None):
    candidate_info = f"\nKandidatens CV:\n\"\"\"{candidate.cv_text}\"\"\"" if candidate else ""

    prompt = f"""
Du är en expert på rekrytering. Här är information om ett jobb:

\"\"\"{job_text}\"\"\" 

Och här är information om en kandidat:

{candidate_info}

Du ska göra följande:

1. Skapa 10 kompetensbaserade intervjufrågor anpassade efter jobbet. Ta gärna hänsyn till kandidatens CV.
2. För varje fråga, skriv vad intervjuaren bör lyssna efter i svaret.
3. Till sist: skriv en sammanfattning till intervjuaren under rubriken "### Tänk på detta".
   Den ska baseras på kandidatens CV – vad som framgår och vad som saknas med tanke på jobbet. 
   Ge konkreta tips på vad man bör följa upp i intervjun, vad som bör förtydligas, och hur kandidaten kan tolkas.

Svara på svenska.
"""

    # 👇 DEBUG: visa vad som skickas in
    print("🧠 PROMPT TILL OPENAI:\n", prompt)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Du är en erfaren HR-specialist."},
            {"role": "user", "content": prompt}
        ]
    )
    full_text = response.choices[0].message.content.strip()

    # 👇 DEBUG: visa vad som kommer tillbaka
    print("✅ SVAR FRÅN OPENAI:\n", full_text)

    if "### Tänk på detta" in full_text:
        questions_part, tips_part = full_text.split("### Tänk på detta", 1)
        questions = questions_part.strip()
        notes = tips_part.strip()
    else:
        questions = full_text
        notes = ""

    return questions, notes