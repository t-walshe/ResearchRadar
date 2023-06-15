from __future__ import annotations
from utils.default_logging import configure_default_logging
from datetime import datetime
import os
from pathlib import Path

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, jsonify
)
from werkzeug.exceptions import abort
import logging
logger = logging.getLogger(__name__)
logger.propagate = True
configure_default_logging(logger, "logs/scout.log")
logger.info(f"Logging initialised from {__name__}")

bp = Blueprint("log", __name__)

# TODO Rewrite this with proper args
@bp.route("/logs/<int:entries>", methods=["GET"])
@bp.route("/logs", defaults={"entries": 0}, methods=["GET"])
def get_latest_logs(entries: int):
    # This shouldn't be hardcoded
    filename: str = "logs/scout.log"
    max_entries: int = 250

    # Limit the number of entries that can be returned
    if (entries > max_entries) or (entries == 0):
        entries = max_entries

    if os.path.exists(filename):
        data: list[str] = Path(filename).read_text().split("\n")
        data: list[str] = [entry for entry in data if entry]

        if len(data) > entries:
            data = data[-entries:]

    else:
        data: list[str] = []

    # Pre-process the strings
    formatted_data: list[dict] = []
    for entry in data:
        items: list[str] = entry.split("-*-")

        if len(items) != 5:
            logger.warning("Entry in log is malformed")

        clean_entry: dict = {}
        clean_entry["time"] = items[0].strip()
        clean_entry["name"] = items[1].strip()
        clean_entry["location"] = items[2].strip()
        clean_entry["level"] = items[3].strip()
        clean_entry["message"] = items[4].strip()
        formatted_data.append(clean_entry)

    return jsonify(formatted_data)
