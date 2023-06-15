from __future__ import annotations
from utils.default_logging import configure_default_logging
from datetime import datetime, timedelta
import os
from utils.typing import PythonScalar
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from db import db, Paper, Metric
import yaml
from pathlib import Path

import pandas as pd

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, jsonify
)

from bokeh.resources import CDN

from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename

import logging
logger = logging.getLogger(__name__)
logger.propagate = True
configure_default_logging(logger, "logs/scout.log")
logger.info(f"Logging initialised from {__name__}")

bp = Blueprint("viewer", __name__)


@bp.route('/')
def index():
    num_papers: int = Paper.query.count()
    current_time: str = datetime.today().strftime('%a %d %b %Y, %I:%M%p')

    # If a graph is available, render it
    filename: str = os.path.join(current_app.instance_path, "formatted_graph.html")
    if os.path.exists(filename):
        graph_data: str = Path(filename).read_text()

        if CDN.js_files:
            cdn_js: str = CDN.js_files[0]
        else:
            cdn_js: str = ""

        if CDN.css_files:
            cdn_css: str = CDN.css_files[0]
        else:
            cdn_css: str = ""
    else:
        graph_data: str = ""
        cdn_js: str = ""
        cdn_css: str = ""

    return render_template("index.html",
                           current_time=current_time,
                           num_papers=f"{num_papers:,}",
                           graph_data=graph_data,
                           cdn_js=cdn_js,
                           cdn_css=cdn_css)


@bp.route('/papers', methods=['GET'])
def get_papers():
    """
    Endpoint used to return arXiv IDs from the database

    Note that the result is [start_date, end_date)

    Example usage
    papers?start_date=01-01-2023&end_date=01-06-2023
    """

    # Get query parameters (defaults to None if not in dict)
    start_date: str | None = request.args.get("start_date")
    end_date: str | None = request.args.get("end_date")

    # If no start date is supplied, default to yesterday, else convert to a datetime object
    if not start_date:
        start_date: datetime = datetime.now() - timedelta(days=1)
    else:
        try:
            start_date: datetime = datetime.strptime(start_date, "%d-%m-%Y")
        except ValueError as e:
            logger.error(e)
            # Return an empty list of IDs and an error code
            return jsonify([]), 500

    # If no end date is supplied, default to now, else convert to a datetime object
    if not end_date:
        end_date: datetime = datetime.now()
    else:
        try:
            end_date: datetime = datetime.strptime(end_date, "%d-%m-%Y")
        except ValueError as e:
            logger.error(e)
            return jsonify([]), 500

    # Using the start and end date, select the relevant IDs from the database
    Session = sessionmaker(bind=db.engine)
    session = Session()
    stmt = select(Paper.arxiv_id).where(Paper.index_date >= start_date, Paper.index_date <= end_date)
    ids: list[str] = sorted([row[0] for row in session.execute(stmt)])
    session.close()

    return jsonify(ids), 200


@bp.route("/upload", methods=["GET", "POST"])
def upload_papers():
    """
    Endpoint that handles the uploading of a CSV file of entries to be added to the paper database
    """
    # Handle the file upload
    if request.method == "POST":
        if "file" not in request.files:
            flash("Failed to handle file, not found")
            return redirect(url_for("index"))

        # Check that the file exists
        file = request.files['file']
        if not file:
            flash("Failed to handle file, not valid")
            return redirect(url_for("index"))

        # Check for an empty filename
        if file.filename == "":
            flash("Failed to handle file, empty filename")
            return redirect(url_for("index"))

        # Check file valid file type
        filename, file_extension = os.path.splitext(file.filename)
        if file_extension != ".csv":
            flash("Failed to handle file, not a CSV")
            return redirect(url_for("index"))

        # Sanitize the filename for logging
        filename: str = secure_filename(file.filename)
        logger.info(f"Handling upload of {filename}")

        # Use Pandas to read the file stream
        df: pd.DataFrame = pd.read_csv(file.stream, dtype={"Id": str, "Date": str})

        # Ensure that the correct columns exist
        necessary_columns: list[str] = ["Id", "Date"]
        for col in necessary_columns:
            if col not in df.columns:
                flash("Failed to handle file, incorrect columns")
                return redirect(url_for("index"))

        # Additional columns can be ignored
        df = df[necessary_columns]

        # Covert column to datetime object
        df["Date"] = pd.to_datetime(df["Date"])

        # De-dupe and store in the database
        retrieved_paper_ids: list[str] = df["Id"].unique().tolist()
        num_added_ids: int = len(retrieved_paper_ids)

        # Start the session
        Session = sessionmaker(bind=db.engine)
        session = Session()

        # Write all IDs to the database
        for index, row in df.iterrows():
            arxiv_id = row["Id"]
            date = row["Date"]
            try:
                paper = Paper(arxiv_id=arxiv_id, index_date=date)
                session.add(paper)
                session.commit()
            except IntegrityError as e:
                # If the item exists, can ignore, don't log
                session.rollback()
                num_added_ids = num_added_ids - 1

        session.close()

        # Message to be displayed on the index page
        logger.info(f"Manually added {len(retrieved_paper_ids)} papers and stored {num_added_ids}")
        flash(f"Uploaded {len(retrieved_paper_ids):,} papers and stored {num_added_ids:,}")
        return redirect(url_for("index"))

    return render_template("upload_csv.html")


@bp.route("/export", methods=["GET"])
def export_papers():
    """
    Endpoint that handles exporting of the entire paper database to a CSV file
    """

    return redirect(url_for("index"))
