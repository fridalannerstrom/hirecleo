import os
import fitz  # PyMuPDF
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import ProfileImageForm
from .models import Profile, ChatSession, ChatMessage
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
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import TestResult
from openai import OpenAI
from PyPDF2 import PdfReader
from .forms import TestChatMessageForm  # valfritt om du vill ha ett formulärobjekt
import uuid
from candidates.models import Candidate
from jobs.models import Job, JobAd

client = OpenAI()

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.Index(os.environ["PINECONE_INDEX"])

# Create your views here.
def dashboard(request):
    return render(request, 'dashboard.html')


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
def chat(request):
    return render(request, 'chat.html')

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


def read_pdf_text(file):
    text = ''
    pdf = PdfReader(file)
    for page in pdf.pages:
        text += page.extract_text() or ''
    return text

@login_required
def upload_test_result(request):
    if request.method == 'POST':
        file = request.FILES.get('uploaded_file')
        test = TestResult(user=request.user, uploaded_file=file)

        # Extrahera text från PDF
        text = read_pdf_text(file)
        test.extracted_text = text

        # Skicka till OpenAI för tolkning
        prompt = f"""
Här är ett testresultat från ett rekryteringstest (t.ex. personlighet, logik, motivation):

\"\"\"{text[:2000]}\"\"\"

Tolka testet och ge en kort sammanfattning om personen – styrkor, utmaningar och vad som sticker ut.
Svara på svenska.
"""
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Du är en rekryteringsexpert som tolkar testresultat."},
                    {"role": "user", "content": prompt}
                ]
            )
            test.ai_summary = response.choices[0].message.content.strip()
        except Exception as e:
            test.ai_summary = "❌ AI-tolkningen misslyckades: " + str(e)

        test.save()
        return redirect('test_result_detail', pk=test.pk)

    return render(request, 'testtolkare-upload.html')


@login_required
def test_result_detail(request, pk):
    test_result = get_object_or_404(TestResult, pk=pk, user=request.user)

    # 🟢 Skapa (eller hämta) en chatt-session för detta test
    session, created = ChatSession.objects.get_or_create(
        user=request.user,
        test_result=test_result,
        defaults={'title': f"Testtolkning {test_result.id}"}
    )

    if request.method == 'POST':
        question = request.POST.get('message')

        prompt = f"""
Detta är resultatet från ett test:

\"\"\"{test_result.extracted_text[:2000]}\"\"\"

Tidigare AI-tolkning:
\"\"\"{test_result.ai_summary}\"\"\"

Fråga från användaren:
\"\"\"{question}\"\"\"

Svara som rekryteringsexpert.
"""
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Du är en AI-expert på psykometriska tester i rekrytering."},
                {"role": "user", "content": prompt}
            ]
        )
        answer = response.choices[0].message.content.strip()

        # 📝 Spara fråga och svar i sessionen
        ChatMessage.objects.create(session=session, sender="user", message=question)
        ChatMessage.objects.create(session=session, sender="cleo", message=answer)

    # 💬 Hämta historiken kopplad till denna test-session
    chat_messages = ChatMessage.objects.filter(session__test_result=test_result).order_by("timestamp")

    return render(request, 'testtolkare-test-result-detail.html', {
        "test_result": test_result,
        "chat_messages": chat_messages
    })


@csrf_exempt
@login_required
def testtolkare_stream_response(request, pk):
    test_result = get_object_or_404(TestResult, pk=pk, user=request.user)

    if request.method != "POST":
        return JsonResponse({"error": "Endast POST tillåtet"}, status=405)

    data = json.loads(request.body)
    user_message = data.get("message", "").strip()

    # Hämta eller skapa session kopplad till testet
    session, _ = ChatSession.objects.get_or_create(
        user=request.user,
        test_result=test_result,
        defaults={'title': f"Testtolkning {test_result.id}"}
    )

    # 📤 Spara frågan direkt (för historik)
    ChatMessage.objects.create(session=session, sender="user", message=user_message)

    prompt = f"""
Detta är resultatet från ett test:

\"\"\"{test_result.extracted_text[:2000]}\"\"\"

Tidigare AI-tolkning:
\"\"\"{test_result.ai_summary}\"\"\"

Fråga från användaren:
\"\"\"{user_message}\"\"\"

Svara som rekryteringsexpert.
"""

    def generate():
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Du är en AI-expert på psykometriska tester i rekrytering."},
                {"role": "user", "content": prompt}
            ],
            stream=True
        )

        accumulated = ""
        for chunk in response:
            delta = chunk.choices[0].delta.content if chunk.choices[0].delta else ""
            if delta:
                accumulated += delta
                yield delta

        # ✅ Spara hela svaret efter streamen är klar
        ChatMessage.objects.create(session=session, sender="cleo", message=accumulated)

    return StreamingHttpResponse(generate(), content_type="text/plain")
