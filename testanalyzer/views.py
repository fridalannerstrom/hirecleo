import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import TestResult
from candidates.models import Candidate
from PyPDF2 import PdfReader
from openai import OpenAI
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

client = OpenAI()

def read_pdf_text(file):
    text = ''
    reader = PdfReader(file)
    for page in reader.pages:
        text += page.extract_text() or ''
    return text

@login_required
def upload_test_result(request):
    if request.method == 'POST':
        file = request.FILES.get('uploaded_file')
        test = TestResult(user=request.user, uploaded_file=file)
        test.extracted_text = read_pdf_text(file)

        prompt = f"""
Här är ett testresultat från ett rekryteringstest:

\"\"\"{test.extracted_text}\"\"\"

Tolka testet och ge en sammanfattning på svenska.
"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Du är en expert på att tolka rekryteringstester."},
                    {"role": "user", "content": prompt}
                ]
            )
            test.ai_summary = response.choices[0].message.content.strip()
        except Exception as e:
            test.ai_summary = f"Fel vid AI-tolkning: {str(e)}"

        test.save()
        return redirect('test_result_detail', pk=test.pk)

    return render(request, 'testanalyzer/upload.html')

@login_required
def test_result_detail(request, pk):
    test_result = get_object_or_404(TestResult, pk=pk, user=request.user)
    return render(request, 'testanalyzer/detail.html', {"test_result": test_result})


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

\"\"\"{test_result.extracted_text}\"\"\"

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
