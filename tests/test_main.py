"""Tests for the application entry point."""

import importlib
import sys


def test_run_invokes_flask_run(monkeypatch, app):
    """The run helper should delegate to Flask's run method."""
    monkeypatch.setattr("init.create_app", lambda: app)
    sys.modules.pop("main", None)
    main = importlib.import_module("main")

    called = {}

    def fake_run(host, port):
        called["host"] = host
        called["port"] = port

    monkeypatch.setattr(main.app, "run", fake_run)

    main.run()

    assert called == {"host": "127.0.0.1", "port": 8000}
