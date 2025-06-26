import os
import re
import json
from PyPDF2 import PdfReader
import fitz  # PyMuPDF

from django.http import (
    HttpResponse,
    JsonResponse,
    StreamingHttpResponse,
    HttpResponseBadRequest
)
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from .models import TestResult, ChatSession, ChatMessage
from candidates.models import Candidate
from jobs.models import Job, JobAd

from django.utils.text import slugify
from unidecode import unidecode
from io import BytesIO


# === Initieringsfunktion ===
def get_clients():
    from openai import OpenAI
    from pinecone import Pinecone

    openai_key = os.environ.get("OPENAI_API_KEY")
    pinecone_key = os.environ.get("PINECONE_API_KEY")
    pinecone_index = os.environ.get("PINECONE_INDEX")

    if not all([openai_key, pinecone_key, pinecone_index]):
        raise EnvironmentError("❌ Nödvändiga API-nycklar saknas.")

    client = OpenAI(api_key=openai_key)
    pc = Pinecone(api_key=pinecone_key)
    index = pc.Index(pinecone_index)

    return client, index


# === PDF-hantering ===

def read_pdf_text(file):
    print("🔍 Startar read_pdf_text...")
    try:
        print("📥 Läser in filen till minne...")
        memory_file = BytesIO(file.read())
        print("✅ Filen inläst till memory_file")

        print("🧪 Försöker PyPDF2...")
        pdf = PdfReader(memory_file)
        text = ''.join(page.extract_text() or '' for page in pdf.pages)
        print(f"📄 PyPDF2 extraherade {len(text)} tecken")
        if text.strip():
            return text
    except Exception as e:
        print("❌ PyPDF2 misslyckades:", e)

    try:
        print("🔁 Försöker fitz (PyMuPDF)...")
        file.seek(0)
        memory_file = BytesIO(file.read())
        doc = fitz.open(stream=memory_file, filetype="pdf")
        text = "\n".join([page.get_text() for page in doc])
        print(f"📄 fitz extraherade {len(text)} tecken")
        return text
    except Exception as e:
        print("❌ fitz också misslyckades:", e)

    print("⚠️ Ingen text kunde extraheras")
    return ""


def normalize_pdf_text(text):
    text = re.sub(r'[ ]{2,}', ' ', text)
    text = re.sub(r'(?<=\w)[ ](?=\w)', '', text)
    text = re.sub(r'\n{2,}', '\n', text)
    return text.strip()


def clean_cv_text(text, phone=None, email=None, linkedin=None):
    for value in [phone, email, linkedin]:
        if value:
            text = re.sub(re.escape(value), '', text)
    text = re.sub(r'\n{2,}', '\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'(?<=[a-zA-Z0-9äöå])\.\s+(?=[A-ZÅÄÖ])', '.\n', text)
    return text.strip()

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


# === AI-tolkning ===

def reformat_cv_text_with_openai(raw_text):
    client, _ = get_clients()
    prompt = f"""
Du är expert på att skriva CV-utdrag från PDF-filer.
Strukturera texten med tydliga rubriker, ta bort formateringsproblem och förkorta innehållet.
Inkludera inte namn, e-post, telefonnummer eller LinkedIn. Skriv på svenska.

{raw_text}
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Du är expert på att tolka och strukturera CV-innehåll."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
        max_tokens=2048
    )
    return response.choices[0].message.content.strip()


def extract_candidate_data_with_openai(text):
    client, _ = get_clients()
    prompt = f"""
Här är innehållet från ett CV:

\"\"\"{text}\"\"\"

Extrahera: Förnamn, Efternamn, E-postadress, Telefonnummer, LinkedIn-länk (om finns), 3 top skills (på svenska), samt en passande *titel* (ex. 'Frontend-utvecklare', 'HR-specialist') baserat på det senaste eller mest relevanta jobbet.

Returnera som JSON med exakt dessa nycklar:
"Förnamn", "Efternamn", "E-postadress", "Telefonnummer", "LinkedIn-länk", "Top Skills", "Titel"
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Du är en duktig CV-analytiker."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=600
    )
    return parse_json_result(response.choices[0].message.content)


def extract_job_data_with_openai(text):
    from openai import OpenAI
    import os

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY is not set.")
    client = OpenAI(api_key=api_key)

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

# === Pinecone ===

def upsert_to_pinecone(doc):
    client, index = get_clients()
    embedding_response = client.embeddings.create(
        model="text-embedding-3-small",
        input=doc.content
    )
    vector = embedding_response.data[0].embedding

    index.upsert(
        vectors=[{
            "id": f"cleo-doc-{doc.id}",
            "values": vector,
            "metadata": {
                "chunk_text": doc.content,
                "title": doc.title
            }
        }],
        namespace="cleo"
    )
    doc.embedding_id = f"cleo-doc-{doc.id}"
    doc.save()
    print(f"✅ Upsertat till Pinecone: cleo-doc-{doc.id} | Titel: {doc.title}")


# === Views ===

@login_required
def chat(request):
    return render(request, 'chat.html')


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
@login_required
def chat_response(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request"}, status=400)

    client, index = get_clients()

    data = json.loads(request.body)
    user_message = data.get("message", "")

    embedding_response = client.embeddings.create(
        model="text-embedding-3-small",
        input=user_message
    )
    user_embedding = embedding_response.data[0].embedding

    pinecone_results = index.query(
        vector=user_embedding,
        top_k=5,
        include_metadata=True,
        namespace="cleo"
    )

    context = "\n\n".join(
        match.metadata.get("chunk_text", "")
        for match in pinecone_results.matches
        if hasattr(match, "metadata") and isinstance(match.metadata, dict)
    )

    def generate():
        messages = [
            {"role": "system", "content": "Du är Cleo, en hjälpsam AI inom rekrytering."},
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


def parse_json_result(result):
    """
    Tar en sträng från OpenAI som kan innehålla ```json-taggar,
    rensar dessa och returnerar resultatet som en Python-dict.
    """
    try:
        # Ta bort ev. ```json-taggar och onödiga whitespace
        cleaned = re.sub(r"```json|```", "", result).strip()
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print("❌ JSONDecodeError i parse_json_result:", e)
        return {}