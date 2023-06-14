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

    return jsonify(data)
