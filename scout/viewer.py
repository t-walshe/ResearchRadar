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

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, jsonify
)

from bokeh.resources import CDN

from werkzeug.exceptions import abort
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
                           num_papers=num_papers,
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

