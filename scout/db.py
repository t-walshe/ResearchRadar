from __future__ import annotations
from flask_sqlalchemy import SQLAlchemy

# Database object is defined as a global variable
db = SQLAlchemy()


# This will be used to create / access a table called paper
class Paper(db.Model):
    arxiv_id = db.Column(db.String, primary_key=True)
    index_date = db.Column(db.TIMESTAMP, nullable=False)
