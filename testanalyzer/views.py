import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import TestResult
from candidates.models import Candidate
from PyPDF2 import PdfReader
from openai import OpenAI

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