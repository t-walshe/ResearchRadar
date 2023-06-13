from __future__ import annotations
from datetime import datetime
import os
from utils.typing import PythonScalar
from flask_sqlalchemy import SQLAlchemy
from db import db, Paper, Metric
import yaml
from pathlib import Path

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)
from werkzeug.exceptions import abort
import logging

from bokeh.resources import CDN

logger = logging.getLogger(__name__)

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

    # TODO Add a manual scrape button to the index.html page
    # TODO Add a log endpoint
    return render_template("index.html",
                           current_time=current_time,
                           num_papers=num_papers,
                           graph_data=graph_data,
                           cdn_js=cdn_js,
                           cdn_css=cdn_css)
