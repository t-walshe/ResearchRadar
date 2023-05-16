from __future__ import annotations
from datetime import datetime
import os

import bs4

from utils.typing import PythonScalar
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
from db import db, Paper
import yaml
import requests
import time
from bs4 import BeautifulSoup


from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort

bp = Blueprint("scrape", __name__)


@bp.route('/scrape')
def scrape():
    """
    Scrape the arXiv IDs for the new papers on each of the
    repositories listed in the config
    """
    config: dict = load_config()
    repositories: list[str] = config.get("repositories", [])
    current_time: str = datetime.now()
    retrieved_paper_ids: list[str] = []

    # TODO Add error handling
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

    for id in retrieved_paper_ids:
        try:
            paper = Paper(arxiv_id=id, index_date=current_time)
            db.session.add(paper)
            db.session.commit()
        except exc.IntegrityError as e:
            # If the item exists, can ignore
            num_added_ids = num_added_ids - 1

    return jsonify({"papers_found": len(retrieved_paper_ids),
                    "papers_added": num_added_ids})


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
