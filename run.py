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
        # get data from form
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        title = request.form.get("title")
        image = request.files["image"]  # upload to server later

        # get candidate database
        with open("data/candidates.json", "r") as json_data:
            candidates = json.load(json_data)

        # create url field
        url = f"{first_name.lower()}-{last_name.lower()}".replace("å", "a").replace("ä", "a").replace("ö", "o")

        # create new candidate
        new_candidate = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "title": title,
            "image_source": "https://t3.ftcdn.net/jpg/02/43/12/34/360_F_243123463_zTooub557xEWABDLk0jJklDyLSGl2jrr.jpg",  # placeholderbild
            "url": url
        }

        # add the candidate
        candidates.append(new_candidate)

        # save database
        with open("data/candidates.json", "w") as json_file:
            json.dump(candidates, json_file, indent=4, ensure_ascii=False)

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


if __name__ == "__main__":
    app.run(
        host=os.environ.get("IP", "0.0.0.0"),
        port=int(os.environ.get("PORT", "5000")),
        debug=True)