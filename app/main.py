"""Entry point for the subweb application.

This module creates the Flask application instance and runs the server.
"""

from init import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
    print("test3")
