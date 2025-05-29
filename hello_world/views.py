import os
import fitz  # PyMuPDF
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import ProfileImageForm
from .models import Candidate, Profile, ChatSession, ChatMessage, Job, JobAd
from django.utils.text import slugify
import uuid
from openai import OpenAI
from PyPDF2 import PdfReader
if os.path.exists("env.py"):
    import env
import re
import markdown
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import StreamingHttpResponse, JsonResponse, HttpResponseBadRequest
from asgiref.sync import sync_to_async
from pinecone import Pinecone
from django.contrib.auth.forms import UserCreationForm
from django.views import View
from django.shortcuts import render, redirect
from bs4 import BeautifulSoup

client = OpenAI()

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.Index(os.environ["PINECONE_INDEX"])

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

class RegisterView(View):
    def get(self, request):
        form = UserCreationForm()
        return render(request, 'auth-register-basic.html', {'form': form})

    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard') 
        return render(request, 'auth-register-basic.html', {'form': form})

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
def your_candidates(request):
    candidates = Candidate.objects.filter(user=request.user).order_by('-created_on')
    return render(request, 'your-candidates.html', {'candidates': candidates})

@login_required
def your_jobs(request):
    jobs = Job.objects.filter(user=request.user).order_by('-created_on')
    return render(request, 'your-jobs.html', {'jobs': jobs})

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

    return render(request, 'add-jobs-manually.html')

@login_required
def add_jobs_pdf(request):
    if request.method == 'POST':
        files = request.FILES.getlist('uploaded_pdf')

        for pdf_file in files:
            job = Job(uploaded_pdf=pdf_file, user=request.user)
            raw_text = read_pdf_text(pdf_file)

            try:
                result = extract_job_data_with_openai(raw_text)
                cleaned = re.sub(r"```json|```", "", result).strip()
                data = json.loads(cleaned)

                job.title = data.get('Titel', '')
                job.company = data.get('Företag', '')
                job.location = data.get('Plats', '')
                job.employment_type = data.get('Anställningsform', '')
                job.description = data.get('Beskrivning', '')
                job.slug = slugify(f"{job.title}-{uuid.uuid4().hex[:6]}")

            except Exception as e:
                print("❌ Error parsing job:", e)

            job.save()

        return redirect('your_jobs')

    jobs = Job.objects.filter(user=request.user).order_by('-created_on')
    return render(request, 'add-jobs-pdf.html', {'jobs': jobs})

@login_required
def chat(request):
    return render(request, 'chat.html')

@login_required
def candidate_detail(request, slug):
    candidate = get_object_or_404(Candidate, slug=slug, user=request.user)
    cv_html = markdown.markdown(candidate.cv_text)
    return render(request, 'your-candidates-profile.html', {
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

    return render(request, 'your-candidates-edit.html', {'candidate': candidate})

@login_required
def delete_candidate(request, slug):
    candidate = get_object_or_404(Candidate, slug=slug, user=request.user)
    candidate.delete()
    return redirect('your_candidates')

def extract_text_from_pdf(pdf_file):
    text = ""
    with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_data_with_openai(text):
    prompt = f"""
    Here is the content from a CV:
    \"\"\"{text}\"\"\"

    Extrahera följande information om kandidaten:
    - Förnamn
    - Efternamn
    - E-postadress
    - Telefonnummer
    - LinkedIn-länk (om det finns)
    - Lista med 3 top skills (som Python, Figma, SQL etc.). På engelska!

    Returnera svaret som ett giltigt JSON-objekt med följande nycklar: "Förnamn", "Efternamn", "E-postadress", "Telefonnummer", "LinkedIn-länk", "Top Skills". Se till att JSON:en är korrekt formatterad utan kommentarer eller extra text.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Du är en duktig CV-analytiker."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )

    return response.choices[0].message.content

def clean_cv_text(text, phone=None, email=None, linkedin=None):
    # Ta bort telefonnummer
    if phone:
        escaped_phone = re.escape(phone)
        text = re.sub(escaped_phone, '', text)

    # Ta bort e-post
    if email:
        escaped_email = re.escape(email)
        text = re.sub(escaped_email, '', text)

    # Ta bort LinkedIn
    if linkedin:
        escaped_linkedin = re.escape(linkedin)
        text = re.sub(escaped_linkedin, '', text)

    # Snygga till radbrytningar och mellanslag
    text = re.sub(r'\n{2,}', '\n', text)  # Max 1 radbrytning
    text = re.sub(r' {2,}', ' ', text)    # Max 1 mellanslag
    text = re.sub(r'(?<=[a-zäöå0-9])\.\s+(?=[A-ZÅÄÖ])', '.\n', text)  # Ny rad efter mening

    return text.strip()

def read_pdf_text(pdf_file):
    pdf = PdfReader(pdf_file)
    text = ''
    for page in pdf.pages:
        text += page.extract_text() or ''
    return text

@login_required
def add_candidates_pdf(request):
    if request.method == 'POST':
        files = request.FILES.getlist('uploaded_pdf')  # ⬅️ direkt från request

        for pdf_file in files:
            candidate = Candidate(uploaded_pdf=pdf_file, user=request.user)

            # 📄 Läs CV-text från PDF
            candidate.cv_text = read_pdf_text(pdf_file)

            # 🧠 Extrahera data med OpenAI
            try:
                import json
                import re

                result = extract_data_with_openai(candidate.cv_text)
                print("🔍 RAW RESULT FROM OPENAI:\n", result)

                cleaned_result = re.sub(r"```json|```", "", result).strip()
                try:
                    data = json.loads(cleaned_result)
                    print("✅ Parsed JSON:\n", data)
                except json.JSONDecodeError as e:
                    print("❌ JSONDecodeError:", e)
                    data = {}

                candidate.first_name = data.get('Förnamn', '')
                candidate.last_name = data.get('Efternamn', '')
                candidate.email = data.get('E-postadress', '')
                candidate.phone_number = data.get('Telefonnummer', '')
                candidate.linkedin_url = data.get('LinkedIn-länk', '')
                candidate.top_skills = data.get('Top Skills', [])

                # 1. Rensa bort kontaktinfo
                candidate.cv_text = clean_cv_text(
                    candidate.cv_text,
                    phone=candidate.phone_number,
                    email=candidate.email,
                    linkedin=candidate.linkedin_url,
                )

                # 2. Skicka till OpenAI för snygg formatering
                candidate.cv_text = reformat_cv_text_with_openai(candidate.cv_text)
            except Exception as e:
                print("🔥 OpenAI error:", e)

            print("💾 Sparar kandidat:", candidate.first_name, candidate.last_name)
            candidate.save()

        return redirect('add_candidates_pdf')

    # GET-request: visa formuläret och befintliga kandidater
    candidates = Candidate.objects.filter(uploaded_pdf__isnull=False).order_by('-created_on')
    return render(request, 'add-candidates-pdf.html', {
        'candidates': candidates
    })


@login_required
def test_openai(request):
    prompt = "Vad heter du?"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return HttpResponse(response.choices[0].message.content)

def reformat_cv_text_with_openai(raw_text):
    prompt = f"""
You are an expert at writing CV excerpts from PDF files. Your task is to structure the text so that it is easy to read and professionally presented. Also make it shorter and more concise.

- Keep all important information
- Divide the text into headings such as: Work experience, Education, Skills, Other
- Remove unnecessary line breaks, incorrect formatting and strange spaces
- Structure it as if it were a real, nice CV
- Do not include name, email, phone number or LinkedIn in the text
- Write in english

Here is the original text:

\"\"\"
{raw_text}
\"\"\"
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an experienced and skilled CV writer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
        max_tokens=2048
    )

    return response.choices[0].message.content.strip()

@csrf_exempt
@login_required
def chat_response(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request"}, status=400)

    data = json.loads(request.body)
    user_message = data.get("message", "")

    # 1. Skapa embedding av användarens fråga
    embedding_response = client.embeddings.create(
        model="text-embedding-3-small",
        input=user_message
    )
    user_embedding = embedding_response.data[0].embedding

    # 2. Hämta kontext från Pinecone
    pinecone_results = index.query(
        vector=user_embedding,
        top_k=5,
        include_metadata=True,
        namespace="cleo"
    )

    # 🔎 Debug: Visa vad vi faktiskt får från Pinecone
    print("🔍 Pinecone-resultat:")
    for match in pinecone_results.matches:
        print("Score:", match.score)
        print("Metadata:", match.metadata)
        print("-" * 40)

    context_chunks = [
        match.metadata.get("chunk_text", "")
        for match in pinecone_results.matches
        if hasattr(match, "metadata") and isinstance(match.metadata, dict)
    ]
    context = "\n\n".join(context_chunks)

    # 3. Streama svaret från GPT med kontext
    def generate():
        messages = [
            {"role": "system", "content": "Du är Cleo, en hjälpsam AI inom rekrytering. Använd kontexten om det är relevant."},
            {"role": "system", "content": f"Kontext:\n{context}"},
            {"role": "user", "content": user_message}
        ]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            stream=True
        )

        for chunk in response:
            delta = chunk.choices[0].delta.content if chunk.choices[0].delta else ""
            if delta:
                yield delta

    return StreamingHttpResponse(generate(), content_type='text/plain')

@csrf_exempt
@login_required
def start_new_session(request):
    if request.method == "POST":
        data = json.loads(request.body)
        title = data.get("title", "Ny konversation")
        session = ChatSession.objects.create(user=request.user, title=title)
        return JsonResponse({"session_id": session.id})
    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
def save_message(request):
    print("🟡 [Django] save_message FUNKTION TRIGGAD:", request.method, request.path)
    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print("📦 Data mottagen:", data)

            session_id = data.get("session_id")
            sender = data.get("sender")
            message = data.get("message")

            session = ChatSession.objects.get(id=session_id, user=request.user)
            ChatMessage.objects.create(
                session=session,
                sender=sender,
                message=message
            )
            print("✅ Meddelande sparat i databasen")
            return JsonResponse({"status": "ok"})

        except Exception as e:
            print("❌ FEL I save_message:", e)
            return JsonResponse({"error": str(e)}, status=500)

    print("❌ Fel metod:", request.method)
    return HttpResponseBadRequest("Invalid request")


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

@login_required
def job_detail(request, slug):
    job = get_object_or_404(Job, slug=slug, user=request.user)
    return render(request, 'your-jobs-detail.html', {'job': job})

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

    return render(request, 'your-jobs-edit.html', {'job': job})

@login_required
def create_jobad(request):
    jobs = Job.objects.filter(user=request.user)

    if request.method == 'POST':
        content = request.POST.get('content')
        job_id = request.POST.get('job') or request.POST.get('job_id')
        job = None

        if job_id:
            job = get_object_or_404(Job, id=job_id, user=request.user)
        else:
            # AI-extraktion baserat på innehåll
            soup = BeautifulSoup(content or "", "html.parser")
            plain_text = soup.get_text()

            try:
                ai_summary_prompt = f"""
                Här är en jobbannons. Extrahera följande information:
                - Titel
                - Företagsnamn
                - Plats
                - Anställningstyp

                Returnera svaret som JSON i formatet:
                {{"title": "...", "company": "...", "location": "...", "employment_type": "..."}}

                Text:
                \"\"\"{plain_text[:2000]}\"\"\"
                """

                ai_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Du är en rekryteringsexpert som extraherar strukturerad information från jobbannonser."},
                        {"role": "user", "content": ai_summary_prompt}
                    ]
                )

                import json
                extracted = json.loads(ai_response.choices[0].message.content)

            except Exception as e:
                print("AI-extraktion misslyckades:", e)
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

        # Spara jobbannonsen
        JobAd.objects.create(
            user=request.user,
            job=job,
            title=job.title,
            content=content,
            is_draft=True
        )

        return redirect('job_detail', slug=job.slug)

    return render(request, 'jobad-create.html', {'jobs': jobs})

@csrf_exempt
@login_required
def generate_jobad_api(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Endast POST tillåtet."}, status=405)

    prompt = request.POST.get("prompt")
    job_id = request.POST.get("job_id")
    uploaded_file = request.FILES.get("job_file")

    # 1. Om ett jobb valts
    if job_id:
        job = get_object_or_404(Job, id=job_id, user=request.user)
        prompt = f"""
        Skapa en jobbannons baserad på detta jobb:
        Titel: {job.title}
        Företag: {job.company}
        Plats: {job.location}
        Anställning: {job.employment_type}
        Beskrivning: {job.description}
        """

    # 2. Om fil laddats upp
    elif uploaded_file:
        from PyPDF2 import PdfReader
        if uploaded_file.name.endswith(".pdf"):
            pdf = PdfReader(uploaded_file)
            text = ''.join(page.extract_text() for page in pdf.pages if page.extract_text())
            prompt = f"Skapa en jobbannons baserat på denna text:\n{text}"
        else:
            text = uploaded_file.read().decode("utf-8", errors="ignore")
            prompt = f"Skapa en jobbannons baserat på denna text:\n{text}"

    if not prompt:
        return JsonResponse({"error": "Ingen input hittades."}, status=400)

    # 3. Skicka till OpenAI
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
        # 1. GPT-output
        content = response.choices[0].message.content.strip()

        # 2. Rensa ev. markdown-block som ```html ... ```
        content = re.sub(r"```html|```", "", content).strip()

        return JsonResponse({"content": content, "suggested_title": "Jobbannons"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    

@login_required
def jobad_detail(request, pk):
    ad = get_object_or_404(JobAd, pk=pk, user=request.user)
    return render(request, 'jobads/jobad_detail.html', {'ad': ad})


@csrf_exempt
@login_required
def compare_candidates(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            job_id = data.get("job_id")
            candidate_ids = data.get("candidate_ids", [])

            if not job_id or not candidate_ids:
                return JsonResponse({"error": "job_id och candidate_ids krävs"}, status=400)

            job = Job.objects.get(id=job_id, user=request.user)
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
Du är en rekryteringsexpert. Baserat på följande jobbannons och information om kandidaten, ge en matchningsscore från 0 till 100.
Förklara också kort varför kandidaten är eller inte är ett bra val.

JOBB:
{job_text}

KANDIDAT:
{summary}

Returnera:
- Score: [en siffra 0–100]
- Kommentar: [en kort sammanfattning]
"""

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Du är en rekryteringsexpert."},
                        {"role": "user", "content": prompt}
                    ]
                )
                ai_reply = response.choices[0].message.content.strip()
                results.append({
                    "candidate_name": f"{candidate.first_name} {candidate.last_name}",
                    "result": ai_reply
                })

            return JsonResponse({"results": results})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Endast POST tillåtet"}, status=405)


@csrf_exempt
@login_required
def compare_candidates_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            job_id = data.get("job_id")
            candidate_ids = data.get("candidate_ids", [])

            if not job_id or not candidate_ids:
                return JsonResponse({"error": "job_id och candidate_ids krävs"}, status=400)

            job = Job.objects.get(id=job_id, user=request.user)
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

Formatet på svaret ska vara:
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

                # Enkel parsing – förväntar sig exakt format
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

    return JsonResponse({"error": "Endast POST tillåtet"}, status=405)

@login_required
def compare_candidates_page(request):
    jobs = Job.objects.filter(user=request.user)
    candidates = Candidate.objects.filter(user=request.user)
    return render(request, "compare-candidates.html", {"jobs": jobs, "candidates": candidates})