from __future__ import annotations
import os
from utils.typing import PythonScalar
from flask_sqlalchemy import SQLAlchemy
from db import db, Paper

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

bp = Blueprint("viewer", __name__)

@bp.route('/')
def index():
    return render_template("index.html")
