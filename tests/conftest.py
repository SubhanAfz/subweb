"""Shared pytest fixtures for the application tests."""

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parent.parent / "app"))

# pylint: disable=wrong-import-position
from init import create_app, db
from models import User

os.environ.setdefault("SECRET_KEY", "testing-secret")


@pytest.fixture(name="test_projects_file")
def _test_projects_file(tmp_path):
    """Create a temporary projects.json file for tests."""
    data = {
        "project1": {
            "title": "Public project",
            "description": "visible",
            "download_link": "/download/public.txt",
            "private": False,
            "role": 0,
        },
        "project2": {
            "title": "Private project",
            "description": "hidden",
            "download_link": "/download/private.txt",
            "private": True,
            "role": 1,
        },
    }
    file_path = tmp_path / "projects.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")
    return file_path


@pytest.fixture(name="test_app")
def _test_app(test_projects_file, tmp_path):
    """Return a configured Flask application for testing."""
    download_dir = tmp_path / "downloads"
    download_dir.mkdir()
    flask_app = create_app(
        {
            "SECRET_KEY": "testing-secret",
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "PROJECTS_JSON_FILE": str(test_projects_file),
            "UPLOAD_FOLDER": str(download_dir),
        }
    )
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture(name="client")
def _client(test_app):
    """Return a test client for the Flask app."""
    return test_app.test_client()


@pytest.fixture(name="user_factory")
def _user_factory(test_app):
    """Factory fixture to create users with different roles."""

    def _create_user(username="user", password="password", role=0):
        with test_app.app_context():
            user = User(username=username, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return {"id": user.id, "username": user.username, "role": user.role}

    return _create_user
