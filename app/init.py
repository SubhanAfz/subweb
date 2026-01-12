"""Application factory for the subweb application."""

import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from jinja2 import select_autoescape


db = SQLAlchemy()


def _env_flag(name: str, default: str = "false") -> bool:
    """Return a boolean for the given environment variable.

    Accepts only "true" (case insensitive) as True, else it is False
    """

    return os.getenv(name, default).lower() in {"true"}


def create_app(test_config=None):
    """Create and configure the Flask application."""
    # pylint: disable=import-outside-toplevel
    from routes import api_bp, main_bp

    app = Flask(__name__)

    secret_key = (test_config or {}).get("SECRET_KEY") or os.environ.get("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY must be set before creating the app.")

    default_config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///users.db",
        "SQLALCHEMY_TRACK_NOTIFICATIONS": False,
        "UPLOAD_FOLDER": os.path.join(app.root_path, "static", "download_files"),
        "PROJECTS_JSON_FILE": os.path.join(app.root_path, "instance", "projects.json"),
        "SQLALCHEMY_SESSION_OPTIONS": {"expire_on_commit": False},
        "DISABLE_LOG_IN": _env_flag("DISABLE_LOG_IN")
    }
    app.config.update(default_config)
    if test_config:
        app.config.update(test_config)
    app.secret_key = secret_key

    app.jinja_env.autoescape = select_autoescape(
        enabled_extensions=("html", "htm", "xml", "jinja"), default=True
    )

    db.init_app(app)

    app.register_blueprint(api_bp)
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()

    return app
