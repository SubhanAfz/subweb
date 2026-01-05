"""Entry point for the subweb application.

This module creates the Flask application instance and runs the server.
"""

from init import create_app

app = create_app()


def run():
    """Run the Flask development server."""
    app.run(host="127.0.0.1", port=8000)


if __name__ == "__main__":  # pragma: no cover
    run()
