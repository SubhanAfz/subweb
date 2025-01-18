
import json
from flask import current_app

def get_project_from_filename(file, projects):
    for project in projects.values():
        if project["download_link"] == f"/download/{file}":
            return project
        
def load_projects():
    with open(current_app.config["PROJECTS_JSON_FILE"], "r") as data:
        return json.load(data)