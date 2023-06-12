from __future__ import annotations
from flask_sqlalchemy import SQLAlchemy

# Database object is defined as a global variable
db = SQLAlchemy()


# Used to create / access a table called paper
class Paper(db.Model):
    arxiv_id = db.Column(db.String, primary_key=True)
    index_date = db.Column(db.TIMESTAMP, nullable=False)


# Used to create / access a table called metric
class Metric(db.Model):
    index_date = db.Column(db.TIMESTAMP, primary_key=True, nullable=False)
    papers_found = db.Column(db.INTEGER, nullable=False)
    papers_added = db.Column(db.INTEGER, nullable=False)
