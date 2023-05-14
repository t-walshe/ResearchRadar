from __future__ import annotations
import os
from utils.typing import PythonScalar
from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from db import db, Paper


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        # DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
        # configure the SQLite database, relative to the app instance folder
        SQLALCHEMY_DATABASE_URI="sqlite:///scout.sqlite",
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # create the extension and initialize the app with the extension
    db.init_app(app)
    with app.app_context():
        db.create_all()

    import viewer
    app.register_blueprint(viewer.bp)
    app.add_url_rule("/", endpoint="index")

    return app


if __name__ == "__main__":
    host: str = "localhost"
    port: int = 4000
    debug: bool = True
    use_reloader: bool = True
    app = create_app()
    app.run(host=host, port=port, debug=debug, use_reloader=use_reloader)
