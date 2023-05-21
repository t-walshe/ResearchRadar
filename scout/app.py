from __future__ import annotations
import os
from utils.typing import PythonScalar
from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from db import db, Paper


def create_app(config=None, instance_path=None) -> Flask:
    """
    Create Flask application

    :param config: Configuration file or object
    :param instance_path: Alternative location of instance directory
    :return: Initialised application
    """

    app = Flask("Scout", instance_path=instance_path, instance_relative_config=True)

    # Ensure that the instance directory exists, if not, create one
    if not os.path.exists(app.instance_path):
        try:
            os.makedirs(app.instance_path)
        except OSError as e:
            exit(-1)

    # Handle configuration and initialisation
    configure_app(app, config)
    configure_blueprints(app)

    return app


def configure_app(app: Flask, config):
    """
    Configure the application

    :param app: Flask application for configuration
    :param config: Nullable config
    """

    # Setup logging
    #configure_logging(app)
    #logger.info("Using config from: {}".format(config_name))

    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI="sqlite:///scout.sqlite",
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )


def configure_blueprints(app: Flask):
    """
    Import and initialise all blueprints

    :param app: Flask application for configuration
    """

    # create the extension and initialize the app with the extension
    db.init_app(app)
    with app.app_context():
        db.create_all()

    import viewer
    app.register_blueprint(viewer.bp)
    app.add_url_rule("/", endpoint="index")

    import scraper
    app.register_blueprint(scraper.bp)
    app.add_url_rule("/scrape", endpoint="scrape")


if __name__ == "__main__":
    host: str = "localhost"
    port: int = 4000
    debug: bool = True
    use_reloader: bool = True
    app = create_app()
    app.run(host=host, port=port, debug=debug, use_reloader=use_reloader)
