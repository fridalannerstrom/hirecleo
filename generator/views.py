from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

@login_required
def create_jobad(request):
    jobs = Job.objects.filter(user=request.user)

    if request.method == 'POST':
        content = request.POST.get('content')
        job_id = request.POST.get('job') or request.POST.get('job_id')
        job = None

        if job_id and job_id.strip() and job_id.strip().isdigit():
            job = get_object_or_404(Job, id=job_id, user=request.user)
        else:
            soup = BeautifulSoup(content or "", "html.parser")
            plain_text = soup.get_text()
            try:
                ai_summary_prompt = f"""
Här är en jobbannons. Extrahera följande information:
- Titel
- Företagsnamn
- Plats
- Anställningstyp

Returnera **endast** ett JSON-objekt:
{{
"title": "Marknadsförare",
"company": "Fridas webbyrå AB",
"location": "Stockholm",
"employment_type": "Heltid"
}}
"""
                ai_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Du är en rekryteringsexpert."},
                        {"role": "user", "content": ai_summary_prompt}
                    ]
                )
                raw_content = ai_response.choices[0].message.content
                json_match = re.search(r'\{.*?\}', raw_content, re.DOTALL)
                if json_match:
                    extracted = json.loads(json_match.group(0))
                else:
                    raise ValueError("Kunde inte hitta JSON i GPT-svaret")
            except Exception:
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
