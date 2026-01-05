"""Tests for helper utilities."""

import json

from utils import get_project_from_filename, load_projects


def test_get_project_from_filename_matches_and_defaults():
    """Ensure matching works and missing entries return None."""
    projects = {
        "one": {"download_link": "/download/one.txt"},
        "two": {"download_link": "/download/two.txt"},
    }

    assert get_project_from_filename("one.txt", projects) == projects["one"]
    assert get_project_from_filename("missing.txt", projects) is None


def test_load_projects_reads_configured_file(test_app, tmp_path, monkeypatch):
    """Verify projects are read from the configured JSON file."""
    override_file = tmp_path / "alt.json"
    override_file.write_text(
        json.dumps({"sample": {"download_link": "/d"}}), encoding="utf-8"
    )
    monkeypatch.setitem(test_app.config, "PROJECTS_JSON_FILE", str(override_file))

    with test_app.app_context():
        data = load_projects()

    assert data == {"sample": {"download_link": "/d"}}
