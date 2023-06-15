from __future__ import annotations
import os
from utils.typing import PythonScalar
from utils.default_logging import configure_default_logging
from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from db import db, Paper
import logging

logger = logging.getLogger(__name__)


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
    configure_logging(app)
    configure_blueprints(app)
    configure_error_handlers(app)

    logger.info("Application launched successfully")

    return app


def configure_app(app: Flask, config):
    """
    Configure the application

    :param app: Flask application for configuration
    :param config: Nullable config
    """

    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI="sqlite:///scout.sqlite",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=16 * 1000 * 1000  # 16 MB max for uploaded files
    )


def configure_logging(app: Flask):
    """
    Setup logging

    :param app: Flask application for configuration
    """

    # Configure
    configure_default_logging(logger, "logs/scout.log")

    # Test the configuration
    logger.info(f"Logging initialised from {__name__}")


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
    app.add_url_rule("/papers", endpoint="get_papers")
    app.add_url_rule("/upload", endpoint="upload_papers")
    app.add_url_rule("/export", endpoint="export_papers")

    import scraper
    app.register_blueprint(scraper.bp)
    app.add_url_rule("/scrape", endpoint="scrape")
    app.add_url_rule("/refresh", endpoint="refresh")

    import log_viewer
    app.register_blueprint(log_viewer.bp)
    app.add_url_rule("/logs", endpoint="get_latest_logs")


def configure_error_handlers(app: Flask):
    """
    Add the error pages

    :param app: Flask application for configuration
    """

    @app.errorhandler(403)
    def forbidden_page(error):
        logger.info("Attempted to access forbidden page")
        return render_template("forbidden_page.html"), 403

    @app.errorhandler(404)
    def page_not_found(error):
        logger.info("Attempted to access page that does not exist")
        return render_template("page_not_found.html"), 404

    @app.errorhandler(500)
    def server_error_page(error):
        logger.info("Server error")
        return render_template("server_error.html"), 500


if __name__ == "__main__":
    host: str = "localhost"
    port: int = 4000
    debug: bool = True
    use_reloader: bool = True
    app = create_app()
    app.run(host=host, port=port, debug=debug, use_reloader=use_reloader)
