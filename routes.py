from flask import Blueprint, render_template, request, session, redirect, url_for, send_from_directory, abort
from init import db
from models import User
from utils import get_project_from_filename, load_projects
import os
import requests

main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__)

@main_bp.route("/")
def index():
    projects = load_projects()
    public_project_count = sum(1 for project in projects.values() if not project["private"])

    loggedIn = "sessionID" in session and "username" in session
    role = User.query.filter_by(username=session["username"]).first().role if loggedIn else -1
    amount_able_to_view = sum(1 for project in projects.values() if project["role"] <= role and project["private"])

    users = User.query.all() if loggedIn else []

    return render_template("index.jinja", title="main page", projects=projects, 
                           public_project_count=public_project_count, loggedIn=loggedIn, 
                           username=session.get("username", ""), role=role, 
                           users=users, amount_able_to_view=amount_able_to_view)

# Login route
@main_bp.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username, password = request.form["username"], request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["sessionID"], session["username"] = user.id, username
            return redirect(url_for("main.index"))
        return render_template("login.jinja", title="login", error="Invalid username or password!")
    
    return render_template("login.jinja", title="login", error="")

# Signup route
@main_bp.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "POST":
        username, password = request.form["username"], request.form["password"]
        if User.query.filter_by(username=username).first():
            return render_template("signup.jinja", title="signup", error="Username already exists!")
        
        new_user = User(username=username)
        new_user.set_password(password)
        new_user.role = 0
        db.session.add(new_user)
        db.session.commit()
        session["sessionID"], session["username"] = new_user.id, username
        return redirect(url_for("main.index"))
    
    return render_template("signup.jinja", title="signup")

# Logout route
@main_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.index"))

# Download route
@main_bp.route("/download/<file>")
def download(file):
    projects = load_projects()
    project = get_project_from_filename(file, projects)

    loggedIn = "sessionID" in session and "username" in session
    role = User.query.filter_by(username=session["username"]).first().role if loggedIn else -1

    if loggedIn and role >= project["role"]:
        try:
            return send_from_directory(os.path.join('static', 'download_files'), file, as_attachment=True)
        except FileNotFoundError:
            abort(404)
    
    return redirect(url_for("main.index"))

# API routes for admin actions
@api_bp.route("/api/changeRole", methods=["POST"])
def changeRole():
    if "username" in session:
        user = User.query.filter_by(username=session["username"]).first()
        if user.role > 99:
            user_to_change = User.query.get(request.form["id"])
            if user_to_change:
                user_to_change.role = request.form["role"]
                db.session.commit()
    return redirect(url_for("main.index"))

@api_bp.route("/api/deleteUser", methods=["POST"])
def deleteUser():
    if "username" in session:
        user = User.query.filter_by(username=session["username"]).first()
        if user.role > 99:
            user_to_delete = User.query.get(request.form["id"])
            if user_to_delete:
                db.session.delete(user_to_delete)
                db.session.commit()
    return redirect(url_for("main.index"))

@api_bp.route("/api/wake", methods=["POST"])
def wake():
    if "username" in session:
        user = User.query.filter_by(username=session["username"]).first()
        if user.role > 99:
            resp = requests.get("http://server-pico_server:5000/wake")
            if resp.ok:
                return "OK"
    return redirect(url_for("main.index"))
