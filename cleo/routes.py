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


@app.route("/upload-candidates", methods=["GET", "POST"])
def upload_candidates():
    if request.method == "POST":
        first_name = Candidate(first_name=request.form.get("first_name"))
        db.session.add(first_name)
        db.session.commit()
        return redirect(url_for("your_candidates"))
    return render_template("upload-candidates.html")


# jobad generator route
@app.route("/jobad-generator")
def jobad():
    return render_template("jobad-generator.html")


# your candidates route
@app.route("/your-candidates")
def your_candidates():
    candidates = list(Candidate.query.order_by(Candidate.first_name).all())
    return render_template("your-candidates.html", candidates=candidates)


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
