import os
import json
from flask import Flask, render_template, request, flash
if os.path.exists("env.py"):
    import env

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

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


# upload candidates route
@app.route("/upload-candidates", methods=["GET", "POST"])
def upload_candidates():
    if request.method == "POST":
        flash("Thanks {}, we have received your message!".format(request.form.get("first_name")))
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


if __name__ == "__main__":
    app.run(
        host=os.environ.get("IP", "0.0.0.0"),
        port=int(os.environ.get("PORT", "5000")),
        debug=True)