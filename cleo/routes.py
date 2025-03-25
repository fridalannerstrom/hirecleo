import os
import json
from flask import Flask, render_template, request, flash
from cleo import app, db
from cleo.models import Candidate, Job
import re
import unicodedata

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


@app.route("/upload-candidates", methods=["GET", "POST"])
def upload_candidates():
    if request.method == "POST":
        # get data from form
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        title = request.form.get("title")
        image = request.files.get("image_source")

        # Spara bilden om den finns
        if image:
            filename = secure_filename(image.filename)
            image_path = os.path.join("static/uploads", filename)
            image.save(image_path)
        else:
            image_path = None

        # skapa slug + se till att den är unik
        base_slug = slugify(f"{first_name} {last_name}")
        url_slug = base_slug
        counter = 1

        while Candidate.query.filter_by(url=url_slug).first():
            counter += 1
            url_slug = f"{base_slug}-{counter}"

        # skapa kandidat
        candidate = Candidate(
            first_name=first_name,
            last_name=last_name,
            email=email,
            title=title,
            image_path=image_path,
            url=url_slug
        )

        db.session.add(candidate)
        db.session.commit()

        flash(f"{first_name} har lagts till i databasen!")

    return render_template("upload-candidates.html")


# jobad generator route
@app.route("/jobad-generator")
def jobad():
    return render_template("jobad-generator.html")


# your candidates route
@app.route("/your-candidates")
def your_candidates():
    data = []
    with open("data/candidates.json", "r") as json_data:
        data = json.load(json_data)
    return render_template("your-candidates.html", candidates=data)


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
