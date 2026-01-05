"""Tests for the application factory."""

import pytest

from init import create_app, db, _env_flag


def test_create_app_uses_provided_config(test_projects_file, tmp_path):
    """Ensure the factory applies a supplied configuration."""
    custom_db = "sqlite://"
    download_dir = tmp_path / "files"
    download_dir.mkdir()

    app = create_app(
        {
            "SECRET_KEY": "override-key",
            "SQLALCHEMY_DATABASE_URI": custom_db,
            "PROJECTS_JSON_FILE": str(test_projects_file),
            "UPLOAD_FOLDER": str(download_dir),
            "TESTING": True,
        }
    )

    assert app.secret_key == "override-key"
    assert app.config["SQLALCHEMY_DATABASE_URI"] == custom_db
    assert app.config["PROJECTS_JSON_FILE"] == str(test_projects_file)
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


def test_env_flag_returns_true_for_true_value(monkeypatch):
    """_env_flag should return True when env var is 'true'."""

    monkeypatch.setenv("TEST_FLAG", "true")
    assert _env_flag("TEST_FLAG") is True

    monkeypatch.setenv("TEST_FLAG", "TRUE")
    assert _env_flag("TEST_FLAG") is True


def test_env_flag_returns_false_for_other_values(monkeypatch):
    """_env_flag should return False for non-'true' values."""

    monkeypatch.setenv("TEST_FLAG", "false")
    assert _env_flag("TEST_FLAG") is False

    monkeypatch.setenv("TEST_FLAG", "1")
    assert _env_flag("TEST_FLAG") is False

    monkeypatch.delenv("TEST_FLAG", raising=False)
    assert _env_flag("TEST_FLAG") is False
