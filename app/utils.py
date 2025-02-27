# pylint: disable=cyclic-import
"""Utility functions for project management in the application."""

import json
from flask import current_app

def get_project_from_filename(filename, projects):
    """
    Retrieve a project based on its download link derived from the filename.

    Args:
        filename (str): The filename to match against project download links.
        projects (dict): A dictionary of projects where each project is a dict
                         with a 'download_link' key.

    Returns:
        dict or None: The matching project if found; otherwise, None.
    """
    for project in projects.values():
        if project.get("download_link") == f"/download/{filename}":
            return project
    return None

def load_projects():
    """
    Load projects from a JSON file specified in the Flask application configuration.

    The JSON file path is read from current_app.config["PROJECTS_JSON_FILE"].

    Returns:
        dict: The loaded JSON data as a Python dictionary.
    """
    config_file = current_app.config.get("PROJECTS_JSON_FILE")
    with open(config_file, "r", encoding="utf-8") as data:
        return json.load(data)
