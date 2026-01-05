"""Routes for the subweb application."""

import os
import requests

from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for,
    send_from_directory,
    abort,
    current_app,
)

from init import db
from models import User
from utils import get_project_from_filename, load_projects

main_bp = Blueprint("main", __name__)
api_bp = Blueprint("api", __name__)
yt_dl_bp = Blueprint("yt_dl", __name__, url_prefix="/yt_dl")


@main_bp.before_app_request
def enforce_disabled_authentication():
    """Clear sessions and block auth routes when authentication is disabled."""
    if not current_app.config.get("DISABLE_LOG_IN", False):
        return None

    if session:
        session.clear()

    if request.endpoint in {"main.login", "main.signup", "main.logout"}:
        return redirect(url_for("main.index"))

    return None


@main_bp.route("/")
def index():
    """
    Render the main page with projects and user data.

    Loads projects from the JSON file, calculates public and accessible
    project counts, and retrieves user info if logged in.
    """
    projects = load_projects()
    public_project_count = sum(
        1 for project in projects.values() if not project["private"]
    )
    disable_log_in = current_app.config.get("DISABLE_LOG_IN", False)
    logged_in = "sessionID" in session and "username" in session
    role = (
        User.query.filter_by(username=session["username"]).first().role
        if logged_in
        else -1
    )
    amount_able_to_view = sum(
        1
        for project in projects.values()
        if project["role"] <= role and project["private"]
    )
    users = User.query.all() if logged_in else []

    return render_template(
        "index.jinja",
        title="main page",
        projects=projects,
        public_project_count=public_project_count,
        loggedIn=logged_in,  # If template expects 'loggedIn', you might need to keep it.
        username=session.get("username", ""),
        role=role,
        users=users,
        amount_able_to_view=amount_able_to_view,
        disable_log_in=disable_log_in,
    )


@main_bp.route("/login", methods=["POST", "GET"])
def login():
    """
    Handle user login.

    On POST, validates credentials and logs in the user. On GET,
    renders the login page.
    """
    if current_app.config.get("DISABLE_LOG_IN", False):
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["sessionID"], session["username"] = user.id, username
            return redirect(url_for("main.index"))
        return render_template(
            "login.jinja", title="login", error="Invalid username or password!"
        )
    return render_template("login.jinja", title="login", error="")


@main_bp.route("/signup", methods=["POST", "GET"])
def signup():
    """
    Handle user signup.

    On POST, creates a new user if the username does not exist. On GET,
    renders the signup page.
    """
    if current_app.config.get("DISABLE_LOG_IN", False):
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if User.query.filter_by(username=username).first():
            return render_template(
                "signup.jinja", title="signup", error="Username already exists!"
            )
        new_user = User(username=username)
        new_user.set_password(password)
        new_user.role = 0
        db.session.add(new_user)
        db.session.commit()
        session["sessionID"], session["username"] = new_user.id, username
        return redirect(url_for("main.index"))

    return render_template("signup.jinja", title="signup")


@main_bp.route("/logout")
def logout():
    """
    Log out the current user and clear the session.
    """
    session.clear()
    return redirect(url_for("main.index"))


@main_bp.route("/download/<file>")
def download(file):
    """
    Handle file download requests.

    Validates user session and role before allowing the download.
    """
    projects = load_projects()
    project = get_project_from_filename(file, projects)

    logged_in = "sessionID" in session and "username" in session
    role = (
        User.query.filter_by(username=session["username"]).first().role
        if logged_in
        else -1
    )

    if logged_in and role >= project["role"]:
        try:
            return send_from_directory(
                os.path.join("static", "download_files"), file, as_attachment=True
            )
        except FileNotFoundError:
            abort(404)
    return redirect(url_for("main.index"))


@api_bp.route("/api/changeRole", methods=["POST"])
def change_role():
    """
    Change the role of a specified user if the current user has admin privileges.
    """
    if "username" in session:
        user = User.query.filter_by(username=session["username"]).first()
        if user.role > 99:
            user_to_change = User.query.get(request.form["id"])
            if user_to_change:
                user_to_change.role = request.form["role"]
                db.session.commit()
    return redirect(url_for("main.index"))


@api_bp.route("/api/wake", methods=["POST"])
def wake():
    """
    Send a wake request to the specified service.

    A timeout is specified to prevent hanging indefinitely.
    """
    if "username" in session:
        user = User.query.filter_by(username=session["username"]).first()
        if user.role > -1:
            resp = requests.post(
                f"http://server-pico_server:5000/wake/{session['username']}", timeout=5
            )
            if resp.ok:
                return "OK"
    return redirect(url_for("main.index"))


@api_bp.route("/api/deleteUser", methods=["POST"])
def delete_user():
    """
    Delete a user if the current user has admin privileges.
    """
    if "username" in session:
        user = User.query.filter_by(username=session["username"]).first()
        if user.role > 99:
            user_to_delete = User.query.get(request.form["id"])
            if user_to_delete:
                db.session.delete(user_to_delete)
                db.session.commit()
    return redirect(url_for("main.index"))
