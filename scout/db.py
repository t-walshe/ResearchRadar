from __future__ import annotations
from flask_sqlalchemy import SQLAlchemy

# Database object is defined as a global variable
db = SQLAlchemy()


# This will be used to create / access a table called paper
class Paper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    upload_date = db.Column(db.TIMESTAMP, nullable=False)
    arxiv_id = db.Column(db.String, unique=True, nullable=False)
