from django.shortcuts import render, redirect
from .models import InterviewPrep
from jobs.models import Job
from candidates.models import Candidate
from core.views import read_pdf_text, normalize_pdf_text
import markdown
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

def clean_markdown(text):
    return text.replace("```markdown", "").replace("```", "").strip()

def prepare_interview(request):
    if request.method == "POST":
        job_id = request.POST.get("job_id")
        candidate_id = request.POST.get("candidate_id")
        free_text = request.POST.get("prompt")
        job_file = request.FILES.get("job_file")

        job = Job.objects.filter(id=job_id).first() if job_id else None
        candidate = Candidate.objects.filter(id=candidate_id).first() if candidate_id else None

        # Kombinera jobbkällor
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
            'result': markdown.markdown(clean_markdown(questions)),
            'candidate': candidate,
            'candidate_summary': markdown.markdown(clean_markdown(notes)),
            'job': job,
        })

    return render(request, 'interviewprep/form.html', {
        'jobs': Job.objects.all(),
        'candidates': Candidate.objects.all()
    })

from openai import OpenAI
client = OpenAI()

def generate_interview_questions(job_text, candidate=None):
    if candidate:
        candidate_info = f"""
        Kandidatens namn: {candidate.first_name} {candidate.last_name}

        Kandidatens CV:
        \"\"\"{candidate.cv_text}\"\"\"
        """
    else:
        candidate_info = ""

    prompt = f"""
    Du är en erfaren HR-specialist. Här är information om ett jobb:

    \"\"\"{job_text}\"\"\" 

    Och här är information om en kandidat:

    {candidate_info}

    Din uppgift är att skapa material inför en kompetensbaserad intervju.

    Gör följande:

    1. Skapa 10 kompetensbaserade intervjufrågor som är relevanta för jobbet.
    2. Formatera varje fråga som en rubrik med `### Fråga 1`, `### Fråga 2`, etc.
    3. Under varje rubrik:
    - Skriv själva frågan i **fetstil**
    - Lägg en tom rad efter frågan
    - Skriv sedan en punktlista där varje punkt börjar med `- Lyssna efter:` följt av vad intervjuaren bör uppmärksamma
    - Avsluta med ett separat stycke som börjar med `🟢 Ett starkt svar innehåller:` och `🔴 Ett svagare svar är:`

    Exempel:

    ### Fråga 1  
    **Beskriv en situation där du...**

    - Lyssna efter: detta  
    - Lyssna efter: det här också

    🟢 Ett starkt svar innehåller...  
    🔴 Ett svagare svar är...

    4. Efter alla frågor, skriv en sammanfattning under rubriken `### Tänk på detta`. Om kandidaten har ett namn, använd namnet. Skriv sammanfattningen baserat på kandidatens CV och jobbet, t ex om det finns
    vissa delar av CVt som behöver beskrivas närmare eller om det finns något i CVt som är extra bra för jobbet eller liknande. Gör så sammanfattningen känns unik för just denna kandidat och detta jobb.

    Svara på **svenska** och använd **korrekt Markdown-format**.
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