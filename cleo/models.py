import os
from cleo import db

class Candidate(db.Model):
    # schema for the Category model
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    title = db.Column(db.String(100))
    image_path = db.Column(db.String(200))
    url = db.Column(db.String(100))  # om du använder URL:er i dina queries
    jobs = db.relationship("Job", backref="candidate", lazy=True)

    def __repr__(self):
        # __repr__ to represent itself in the form of a string
        return self.candidate_name


class Job(db.Model):
    # schema for the Task model
    id = db.Column(db.Integer, primary_key=True)
    job_title = db.Column(db.String(50), unique=True, nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    is_urgent = db.Column(db.Boolean, default=False, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidate.id"), nullable=False)

    def __repr__(self):
        # __repr__ to represent itself in the form of a string
        return "#{0} - Job: {1} | Urgent: {2}".format(
            self.id, self.job_title, self.is_urgent
        )