import os
import json
from flask import Flask, render_template, request, flash
from flask_sqlalchemy import SQLAlchemy
import psycopg2
if os.path.exists("env.py"):
    import env  # noqa

DATABASE_URL = os.environ['DATABASE_URL']

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
app.secret_key = os.environ.get("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///local.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

from cleo import routes  # noqa