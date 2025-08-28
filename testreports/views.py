from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import TestReport
from core.views import read_pdf_text

@login_required
def your_testreports(request):
    reports = TestReport.objects.filter(user=request.user).order_by('-created_on')
    return render(request, 'testreports/your-testreports.html', {'reports': reports})

@login_required
def upload_testreport(request):
    if request.method == "POST":
        file = request.FILES.get("uploaded_file")
        if file:
            report = TestReport.objects.create(user=request.user, uploaded_file=file)
            raw_text = read_pdf_text(file)
            report.extracted_text = raw_text

            # AI summary (if you want to auto-generate here)
            try:
                report.summary = summary
            except Exception as e:
                print("❌ AI failed:", e)

            report.save()
            return redirect('your_testreports')

    return render(request, 'testreports/upload-testreport.html')

@login_required
def testreport_detail(request, id):
    report = get_object_or_404(TestReport, id=id, user=request.user)
    return render(request, 'testreports/testreport-detail.html', {'report': report})