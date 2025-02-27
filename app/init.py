"""Application factory for the subweb application."""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Initialise configuration variables
    app.secret_key = os.environ["SECRET_KEY"]
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
    app.config["SQLALCHEMY_TRACK_NOTIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, 'static', 'download_files')
    app.config["PROJECTS_JSON_FILE"] = os.path.join(app.root_path, 'instance', 'projects.json')

    db.init_app(app)
    from routes import api_bp, main_bp, yt_dl_bp  # pylint: disable=import-outside-toplevel
    app.register_blueprint(api_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(yt_dl_bp)

    with app.app_context():
        db.create_all()

    return app
