import os
import json
from flask import Flask, render_template, request, flash, redirect, url_for
from cleo import app
import re
import unicodedata
from cleo.models import Candidate, Job, db

def slugify(value):
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s]+", "-", value)

# Index route with candidate database
@app.route("/")
def index():
    data = []
    with open("data/candidates.json", "r") as json_data:
        data = json.load(json_data)
    return render_template("index.html", candidates=data)


# About route
@app.route("/about")
def about():
    return render_template("about.html")

# Upload candidates route
@app.route("/upload-candidates", methods=["GET", "POST"])
def upload_candidates():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        title = request.form.get("title")
        image_path = request.form.get("image_path")

        new_candidate = Candidate(first_name=first_name, last_name=last_name, email=email, title=title, image_path=image_path)
        new_candidate.url = slugify(f"{first_name}-{last_name}")
        # Check if the candidate already exists
        existing_candidate = Candidate.query.filter_by(email=email).first()
        if existing_candidate:
            flash("Candidate already exists!", "error")
            return redirect(url_for("upload_candidates"))
        # Add the new candidate to the database
        if not first_name or not last_name or not email or not title:
            flash("All fields are required!", "error")
            return redirect(url_for("upload_candidates"))
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Invalid email address!", "error")
            return redirect(url_for("upload_candidates"))
        if not title:
            flash("Title is required!", "error")
            return redirect(url_for("upload_candidates"))
        if not first_name:
            flash("First name is required!", "error")
            return redirect(url_for("upload_candidates"))
        if not last_name:
            flash("Last name is required!", "error")
            return redirect(url_for("upload_candidates"))
        if not email:
            flash("Email is required!", "error")
            return redirect(url_for("upload_candidates"))
        db.session.add(new_candidate)
        db.session.commit()

        return redirect(url_for("your_candidates"))
    
    return render_template("upload-candidates.html")

# Edit candidate route
@app.route("/edit_candidate/<int:candidate_id>", methods=["GET", "POST"])
def edit_candidate(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)

    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        title = request.form.get("title")
        image_path = request.form.get("image_path")

        # Validering
        if not first_name or not last_name or not email or not title:
            flash("All fields are required!", "error")
            return redirect(url_for("edit_candidate", candidate_id=candidate.id))
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Invalid email address!", "error")
            return redirect(url_for("edit_candidate", candidate_id=candidate.id))

        # Kontrollera om e-postadressen används av någon annan kandidat
        existing_candidate = Candidate.query.filter_by(email=email).first()
        if existing_candidate and existing_candidate.id != candidate.id:
            flash("Another candidate with this email already exists!", "error")
            return redirect(url_for("edit_candidate", candidate_id=candidate.id))

        # Uppdatera kandidatens data
        candidate.first_name = first_name
        candidate.last_name = last_name
        candidate.email = email
        candidate.title = title
        candidate.image_path = image_path
        candidate.url = slugify(f"{first_name}-{last_name}")

        db.session.commit()
        flash("Candidate updated successfully!", "success")
        return redirect(url_for("your_candidates"))

    return render_template("edit-candidate.html", candidate=candidate)

# Delete candidate route
@app.route("/delete_candidate/<int:candidate_id>")
def delete_candidate(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    db.session.delete(candidate)
    db.session.commit()
    return redirect(url_for("your_candidates"))

# Delete job route
@app.route("/delete_job/<int:job_id>")
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    return redirect(url_for("your_jobs"))
  

# jobad generator route
@app.route("/jobad-generator")
def jobad():
    return render_template("jobad-generator.html")


# your candidates route
@app.route("/your-candidates")
def your_candidates():
    candidates = list(Candidate.query.order_by(Candidate.first_name).all())
    return render_template("your-candidates.html", candidates=candidates)

# your jobs route
@app.route("/your-jobs")
def your_jobs():
    jobs = list(Job.query.order_by(Job.title).all())
    return render_template("your-jobs.html", jobs=jobs)

# candidate page route
@app.route("/your-candidates/<candidate_name>")
def about_candidate(candidate_name):
    candidate = {}
    with open("data/candidates.json", "r") as json_data:
        data = json.load(json_data)
        for obj in data:
            if obj["url"] == candidate_name:
                candidate = obj
    return render_template("candidate.html", candidate=candidate)


# Upload jobs route
@app.route("/upload-jobs", methods=["GET", "POST"])
def upload_jobs():
    candidates = list(Candidate.query.order_by(Candidate.first_name).all())
    if request.method == "POST":
        job = Job(
            title=request.form.get("title"),
            description=request.form.get("description"),
            is_urgent=bool(True if request.form.get("is_urgent") else False),
            due_date=request.form.get("due_date"),
            candidate_id=request.form.get("candidate_id")
        )
        db.session.add(job)
        db.session.commit()
        return redirect(url_for("your_jobs"))
    return render_template("upload-jobs.html", candidates=candidates)

# Edit jobs route
@app.route("/edit-job/<int:job_id>", methods=["GET", "POST"])
def edit_job(job_id):
    candidates = list(Candidate.query.order_by(Candidate.first_name).all())
    job = Job.query.get_or_404(job_id)

    if request.method == "POST":
        title=request.form.get("title"),
        description=request.form.get("description"),
        is_urgent=bool(True if request.form.get("is_urgent") else False),
        due_date=request.form.get("due_date"),

        # Uppdatera kandidatens data
        job.title = title
        job.description = description
        is_urgent = 'is_urgent' in request.form
        job.due_date = due_date
        job.url = slugify(f"{title}")

        db.session.commit()
        flash("Job updated successfully!", "success")
        return redirect(url_for("your_jobs"))

    return render_template("edit-job.html", job=job)


@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'Candidate': Candidate,
        'Job': Job,
    }