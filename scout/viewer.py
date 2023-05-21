from __future__ import annotations
from datetime import datetime
import os
from utils.typing import PythonScalar
from flask_sqlalchemy import SQLAlchemy
from db import db, Paper
import yaml

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
import logging

logger = logging.getLogger(__name__)

bp = Blueprint("viewer", __name__)


@bp.route('/')
def index():
    num_papers: int = Paper.query.count()
    current_time: str = datetime.today().strftime('%a %d %b %Y, %I:%M%p')
    return render_template("index.html",
                           current_time=current_time,
                           num_papers=num_papers)
