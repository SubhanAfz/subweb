"""Tests for the application factory."""

import pytest

from init import create_app, db


def test_create_app_uses_provided_config(projects_file, tmp_path):
    """Ensure the factory applies a supplied configuration."""
    custom_db = "sqlite://"
    download_dir = tmp_path / "files"
    download_dir.mkdir()

    app = create_app(
        {
            "SECRET_KEY": "override-key",
            "SQLALCHEMY_DATABASE_URI": custom_db,
            "PROJECTS_JSON_FILE": str(projects_file),
            "UPLOAD_FOLDER": str(download_dir),
            "TESTING": True,
        }
    )

    assert app.secret_key == "override-key"
    assert app.config["SQLALCHEMY_DATABASE_URI"] == custom_db
    assert app.config["PROJECTS_JSON_FILE"] == str(projects_file)
    assert app.config["UPLOAD_FOLDER"] == str(download_dir)

    with app.app_context():
        db.create_all()
        tables = db.inspect(db.engine).get_table_names()
    assert "user" in tables


def test_create_app_requires_secret_key(monkeypatch):
    """The factory should fail if no secret key is available."""
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError):
        create_app()


def test_create_app_uses_environment(monkeypatch, tmp_path):
    """Environment variables should populate defaults when no config is given."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SECRET_KEY", "env-key")

    app = create_app()

    assert app.secret_key == "env-key"
    assert app.config["SQLALCHEMY_DATABASE_URI"].endswith("users.db")
