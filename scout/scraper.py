from __future__ import annotations
from utils.default_logging import configure_default_logging
from math import pi
from datetime import datetime
import os

import bs4

from utils.typing import PythonScalar
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from db import db, Paper, Metric
import yaml
import requests
import time

from pathlib import Path
from bokeh.plotting import figure, show, output_file, save
from bs4 import BeautifulSoup

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify, current_app
)
from werkzeug.exceptions import abort
import logging
logger = logging.getLogger(__name__)
logger.propagate = True
configure_default_logging(logger, "logs/scout.log")
logger.info(f"Logging initialised from {__name__}")

bp = Blueprint("scrape", __name__)


@bp.route('/scrape')
def scrape():
    """
    Scrape the arXiv IDs for the new papers on each of the
    repositories listed in the config
    """
    config: dict = load_config()
    repositories: list[str] = config.get("repositories", [])
    current_time: datetime = datetime.now()
    retrieved_paper_ids: list[str] = []

    # TODO Add error handling and logging
    for repository in repositories:
        # This could be improved by making the requests async or non-blocking
        time.sleep(config.get("seconds_per_request", 4))

        # All new, cross-listed, and replaced papers
        url: str = f"https://arxiv.org/list/{repository}/new"

        # Content can be extracted from the page HTML
        r: requests.Response = requests.get(url, timeout=10)

        # Extract the new arXiv IDs
        if r.status_code == 200:
            paper_ids: list[str] = extract_paper_ids(r.content, include=config.get("targets", []))
        else:
            paper_ids: list[str] = []

        retrieved_paper_ids.extend(paper_ids)

    # De-dupe and store in the database
    retrieved_paper_ids: list[str] = list(set(retrieved_paper_ids))
    num_added_ids: int = len(retrieved_paper_ids)

    # Start the session
    Session = sessionmaker(bind=db.engine)
    session = Session()

    # Write all IDs to the database
    for id in retrieved_paper_ids:
        try:
            paper = Paper(arxiv_id=id, index_date=current_time)
            session.add(paper)
            session.commit()
        except IntegrityError as e:
            # If the item exists, can ignore, don't log
            session.rollback()
            num_added_ids = num_added_ids - 1

    # Add metrics to database
    try:
        metric = Metric(index_date=current_time,
                        papers_found=len(retrieved_paper_ids),
                        papers_added=num_added_ids)
        session.add(metric)
        session.commit()
    except IntegrityError as e:
        # If a metric with the same timestamp exists, ignore and rollback
        session.rollback()

    session.close()

    # Regenerate the graphs
    res: bool = render_metrics_to_bokeh()
    logger.info(f"Regenerating metrics visualisation")
    logger.info(f"Found {len(retrieved_paper_ids)} paper and stored {num_added_ids}")

    return redirect(url_for("index"))


@bp.route('/refresh')
def refresh():
    """
    Refresh / regenerate any visualisations
    """

    res: bool = render_metrics_to_bokeh()
    logger.info(f"Regenerating metrics visualisation")
    return redirect(url_for("index"))


def load_config() -> dict:
    with open("config/config.yml", "r") as file:
        config = yaml.safe_load(file)
    return config


def extract_paper_ids(content: bytes, include: list[str] | None = None) -> list[str]:
    # Parse the HTML
    soup = BeautifulSoup(content, 'html.parser')

    # Find all elements with class "list-identifier"
    identifier_elements: list[bs4.Tag] = soup.find_all(class_="list-identifier")
    identifier_text: list[str] = [tag.text for tag in identifier_elements]

    new_ids: list[str] = []
    cross_list_ids: list[str] = []
    replaced_ids: list[str] = []

    for id_text in identifier_text:
        # Extract the ID
        if id_text:
            id: str = id_text.split(" ")[0]

            if id:
                id: str = id.split(":")[-1]
        else:
            id: str = ""

        if "cross-list" in id_text:
            if id:
                cross_list_ids.append(id)
        elif "replaced" in id_text:
            if id:
                replaced_ids.append(id)
        else:
            if id:
                new_ids.append(id)

    # Gather the IDs to be returned
    ids: list[str] = []
    if include:
        if "new" in include:
            ids.extend(new_ids)

        if "cross-list" in include:
            ids.extend(cross_list_ids)

        if "replaced" in include:
            ids.extend(replaced_ids)

        ids: list[str] = list(set(ids))

    return ids


def render_metrics_to_bokeh() -> bool:
    """
    Read the metrics table and render as a bar chart saved in the instance folder
    """

    # Sort by index date and return the entire table
    # TODO Update to newer select method
    metrics: list[Metric] = Metric.query.order_by(Metric.index_date.asc()).all()

    if not metrics:
        return False

    dates: list[str] = [metric.index_date.strftime("%d/%m/%y %H:%M:%S") for metric in metrics]
    papers_found: list[int] = [metric.papers_found for metric in metrics]
    papers_added: list[int] = [metric.papers_added for metric in metrics]

    data: dict = {"dates": dates,
                  "Found": papers_found,
                  "Added": papers_added}

    p = figure(x_range=dates,
               height=512,
               max_width=int(512 * 1.4),
               sizing_mode="scale_width",
               title="Scraping metrics",
               toolbar_location=None)

    p.vbar(x="dates", top="Found", width=0.9, line_width=0, source=data, legend_label="Found", color="#718dbf")
    p.vbar(x="dates", top="Added", width=0.9, line_width=0, source=data, legend_label="Added", color="#FFB4B4")

    p.xaxis.major_label_orientation = pi/3
    p.y_range.start = 0
    p.x_range.range_padding = 0.1
    p.xgrid.grid_line_color = None
    p.axis.minor_tick_line_color = None
    p.outline_line_color = None
    p.legend.location = "top_left"
    p.legend.orientation = "horizontal"
    p.legend.click_policy = "hide"

    # set output to static HTML file - change these as desired
    filename = os.path.join(current_app.instance_path, 'unformatted_graph.html')
    output_file(filename=filename, title="Static HTML file")
    _ = save(p)

    # Load the generated plot, extract the body, place in container
    parsed_html = BeautifulSoup(Path(filename).read_text(), "html.parser")
    body = parsed_html.find('body')

    content: list = [str(tag) for tag in body.contents]
    content.insert(0, '<div class="container" style="display: flex; justify-content: center;">')
    content.append('</div>')

    filename = os.path.join(current_app.instance_path, 'formatted_graph.html')
    _ = Path(filename).write_text(" ".join(content))

    return True
