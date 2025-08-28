from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import TestReport
from core.views import read_pdf_text, get_clients
import json
import traceback

@login_required
def your_testreports(request):
    reports = TestReport.objects.filter(user=request.user).order_by('-created_on')
    return render(request, 'testreports/your-testreports.html', {'reports': reports})

@login_required
def testreport_detail(request, id):
    report = get_object_or_404(TestReport, id=id, user=request.user)
    return render(request, 'testreports/testreport-detail.html', {'report': report})


@login_required
def upload_testreport(request):
    if request.method == "POST":
        file = request.FILES.get("uploaded_file")
        if file:
            report = TestReport.objects.create(user=request.user, uploaded_file=file)

            try:
                print("📥 Startar read_pdf_text...")
                raw_text = read_pdf_text(file)
                report.extracted_text = raw_text

                if not raw_text.strip():
                    raise ValueError("Ingen text kunde extraheras från filen.")

                # 🔎 Metadata (typ + 1-radssammanfattning)
                try:
                    ai_json = analyze_test_metadata_with_ai(raw_text[:8000])  # klipp om lång
                    print("🔎 AI metadata svar:", ai_json)
                    import re

                    # Ta bort ev. markdown-formattering (```json ... ```)
                    clean_json = re.sub(r"^```json|```$", "", ai_json.strip()).strip()

                    parsed = json.loads(clean_json)
                    report.test_type = parsed.get("test_type", "").strip()
                    report.short_summary = parsed.get("short_summary", "").strip()
                except Exception as e:
                    print("❌ Fel i metadata-analys:")
                    traceback.print_exc()
                    messages.warning(request, f"Kunde inte analysera testtyp eller sammanfatta kort.")

                # 🧠 Full AI-sammanfattning
                try:
                    summary = summarize_test_report_with_ai(raw_text)
                    if summary:
                        report.summary = summary
                        print("🧠 Full summary skapad.")
                    else:
                        print("⚠️ GPT gav inget svar för summary.")
                        messages.warning(request, "AI kunde inte generera en fullständig sammanfattning.")
                except Exception as e:
                    print("❌ Fel i fullständig AI-sammanfattning:")
                    traceback.print_exc()
                    messages.warning(request, f"Kunde inte skapa AI-sammanfattning.")

                report.save()
                messages.success(request, "Testrapporten laddades upp med AI-analys!")

            except Exception as e:
                print("❌ Allmänt fel vid uppladdning:")
                traceback.print_exc()
                messages.error(request, f"Något gick fel: {e}")

            return redirect('your_testreports')

    return render(request, 'testreports/upload-testreport.html')


def summarize_test_report_with_ai(text):
    client, _ = get_clients()
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Du är en expert på att analysera psykometriska testresultat i rekrytering."},
                {"role": "user", "content": f"""
Analysera följande testresultat:

\"\"\"{text}\"\"\"

Sammanfatta:
- Styrkor
- Eventuella utvecklingsområden
- Arbetsstil och lämplighet
- En övergripande rekommendation

Skriv professionellt, punktformat, och på svenska.
"""}
            ],
            max_tokens=800
        )
        if response.choices:
            return response.choices[0].message.content.strip()
        return ""
    except Exception as e:
        print("❌ GPT-fel i summarize_test_report_with_ai:", e)
        return ""


def analyze_test_metadata_with_ai(text):
    client, _ = get_clients()
    try:
        prompt = f"""
            Texten nedan är innehållet i ett psykometriskt testresultat.

            \"\"\"{text}\"\"\"

            1. Vad är det för typ av test? (ex: Personlighetstest, Logiskt test, Färdighetstest)
            2. Sammanfatta testets slutsats i en enda mening.

            Svara exakt i detta JSON-format, utan några förklaringar eller markdown-taggar:
            {{"test_type": "...", "short_summary": "..."}}
            """
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400
        )
        if response.choices:
            return response.choices[0].message.content.strip()
        return '{"test_type": "", "short_summary": ""}'
    except Exception as e:
        print("❌ GPT-fel i analyze_test_metadata_with_ai:", e)
        return '{"test_type": "", "short_summary": ""}'
