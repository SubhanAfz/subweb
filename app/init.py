from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import os



db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    #initalise config vars into the application
    app.secret_key = os.environ["SECRET_KEY"]
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
    app.config["SQLALCHEMY_TRACK_NOTIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, 'static', 'download_files')
    app.config["PROJECTS_JSON_FILE"] = os.path.join(app.root_path, 'instance', 'projects.json')
    

    db.init_app(app)
    from routes import api_bp, main_bp
    app.register_blueprint(api_bp)
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()

    return app
