"""Route-level integration tests."""

from pathlib import Path

from init import db
from models import User
from utils import get_project_from_filename


def test_index_counts_projects(client):
    """Index should render with public project count for anonymous users."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"My public projects (1)" in response.data
    assert b"to view private projects you must log in" in response.data


def test_index_for_logged_in_user(client, user_factory):
    """Logged-in users should see private project messaging."""
    user = user_factory(username="private_user", role=2)
    with client.session_transaction() as sess:
        sess["sessionID"] = user["id"]
        sess["username"] = user["username"]

    response = client.get("/")

    assert response.status_code == 200
    assert b"My private projects (1)" in response.data
    assert b"wakeButton" in response.data


def test_signup_creates_user(client):
    """Signing up a new account stores it in the database."""
    response = client.post(
        "/signup",
        data={"username": "new_user", "password": "pw"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert db.session.query(User).filter_by(username="new_user").one()


def test_signup_duplicate_username(client, user_factory):
    """Attempting to reuse a username should show an error."""
    user_factory(username="dupe", password="pw")

    response = client.post(
        "/signup",
        data={"username": "dupe", "password": "pw"},
        follow_redirects=True,
    )

    assert b"Username already exists" in response.data


def test_signup_get(client):
    """GET signup should render the form without errors."""
    response = client.get("/signup")
    assert response.status_code == 200
    assert b"signup" in response.data


def test_login_success_and_failure(client, user_factory):
    """Login shows errors for bad credentials and succeeds for correct ones."""
    user_factory(username="login_user", password="pw")

    bad = client.post(
        "/login",
        data={"username": "login_user", "password": "wrong"},
        follow_redirects=True,
    )
    assert b"Invalid username or password" in bad.data

    good = client.post(
        "/login",
        data={"username": "login_user", "password": "pw"},
        follow_redirects=False,
    )
    assert good.status_code == 302
    with client.session_transaction() as sess:
        assert sess["username"] == "login_user"


def test_login_get(client):
    """GET login renders an empty form."""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"login" in response.data


def test_logout_clears_session(client):
    """Logout should remove session data."""
    with client.session_transaction() as sess:
        sess["username"] = "someone"
        sess["sessionID"] = 1

    response = client.get("/logout")

    assert response.status_code == 302
    with client.session_transaction() as sess:
        assert "username" not in sess
        assert "sessionID" not in sess


def test_download_allows_authorized_user(app, client, user_factory):
    """Authorized users can download files from the configured folder."""
    user = user_factory(username="downloader", role=1)
    with client.session_transaction() as sess:
        sess["username"] = user["username"]
        sess["sessionID"] = user["id"]

    private_file = Path(app.config["UPLOAD_FOLDER"]) / "private.txt"
    private_file.write_text("secret data", encoding="utf-8")

    response = client.get("/download/private.txt")

    assert response.status_code == 200
    assert response.data == b"secret data"


def test_download_handles_missing_file(app, client, user_factory, monkeypatch):
    """Missing files should produce a 404 error when access is allowed."""
    user = user_factory(username="missing", role=1)
    with client.session_transaction() as sess:
        sess["username"] = user["username"]
        sess["sessionID"] = user["id"]

    def raise_missing(*_args, **_kwargs):
        raise FileNotFoundError

    monkeypatch.setattr("routes.send_from_directory", raise_missing)

    response = client.get("/download/private.txt")

    assert response.status_code == 404


def test_download_redirects_when_not_logged_in(client):
    """Anonymous users are redirected away from downloads."""
    response = client.get("/download/private.txt")
    assert response.status_code == 302


def test_change_role_updates_user(client, user_factory):
    """Admins should be able to change another user's role."""
    admin = user_factory(username="admin", role=100)
    target = user_factory(username="target", role=0)

    with client.session_transaction() as sess:
        sess["username"] = admin["username"]
        sess["sessionID"] = admin["id"]

    response = client.post(
        "/api/changeRole",
        data={"id": target["id"], "role": 5},
        follow_redirects=False,
    )

    assert response.status_code == 302
    with client.application.app_context():
        assert db.session.get(User, target["id"]).role == 5


def test_change_role_no_admin_redirects(client, user_factory):
    """Non-admin users should not be able to change roles."""
    regular = user_factory(username="regular", role=0)
    target = user_factory(username="target2", role=0)

    with client.session_transaction() as sess:
        sess["username"] = regular["username"]
        sess["sessionID"] = regular["id"]

    response = client.post(
        "/api/changeRole",
        data={"id": target["id"], "role": 5},
        follow_redirects=False,
    )

    assert response.status_code == 302
    with client.application.app_context():
        assert db.session.get(User, target["id"]).role == 0


def test_wake_authorized_user(monkeypatch, client, user_factory):
    """A successful wake call should return OK."""
    caller = user_factory(username="caller", role=1)
    with client.session_transaction() as sess:
        sess["username"] = caller["username"]
        sess["sessionID"] = caller["id"]

    called = {}

    class FakeResponse:
        ok = True

    def fake_post(url, timeout):
        called["url"] = url
        called["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("routes.requests.post", fake_post)

    response = client.post("/api/wake")

    assert response.status_code == 200
    assert response.data == b"OK"
    assert called["url"].endswith(f"/wake/{caller['username']}")
    assert called["timeout"] == 5


def test_wake_redirects_when_not_logged_in(client):
    """Unauthorized wake calls should redirect."""
    response = client.post("/api/wake")
    assert response.status_code == 302


def test_delete_user_removes_target(client, user_factory):
    """Admins can delete users."""
    admin = user_factory(username="admin_del", role=100)
    target = user_factory(username="victim", role=0)

    with client.session_transaction() as sess:
        sess["username"] = admin["username"]
        sess["sessionID"] = admin["id"]

    response = client.post(
        "/api/deleteUser",
        data={"id": target["id"]},
        follow_redirects=False,
    )

    assert response.status_code == 302
    with client.application.app_context():
        assert db.session.get(User, target["id"]) is None


def test_delete_user_without_admin(client, user_factory):
    """Non-admin deletion attempts should leave users intact."""
    regular = user_factory(username="regular_del", role=0)
    target = user_factory(username="target_del", role=0)

    with client.session_transaction() as sess:
        sess["username"] = regular["username"]
        sess["sessionID"] = regular["id"]

    response = client.post(
        "/api/deleteUser",
        data={"id": target["id"]},
        follow_redirects=False,
    )

    assert response.status_code == 302
    with client.application.app_context():
        assert db.session.get(User, target["id"]) is not None


def test_get_project_from_filename_integration(app):
    """Integration check for matching projects through filename."""
    with app.app_context():
        projects = get_project_from_filename(
            "public.txt", {"public": {"download_link": "/download/public.txt"}}
        )

    assert projects == {"download_link": "/download/public.txt"}


def test_disabled_auth_clears_session(app, client):
    """When DISABLE_LOG_IN is True, sessions are cleared on request."""
    app.config["DISABLE_LOG_IN"] = True

    with client.session_transaction() as sess:
        sess["username"] = "someone"
        sess["sessionID"] = 1

    client.get("/")

    with client.session_transaction() as sess:
        assert "username" not in sess
        assert "sessionID" not in sess


def test_disabled_auth_redirects_login(app, client):
    """When DISABLE_LOG_IN is True, /login redirects to index."""
    app.config["DISABLE_LOG_IN"] = True

    response = client.get("/login")

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_disabled_auth_redirects_signup(app, client):
    """When DISABLE_LOG_IN is True, /signup redirects to index."""
    app.config["DISABLE_LOG_IN"] = True

    response = client.get("/signup")

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_disabled_auth_redirects_logout(app, client):
    """When DISABLE_LOG_IN is True, /logout redirects to index."""
    app.config["DISABLE_LOG_IN"] = True

    response = client.get("/logout")

    assert response.status_code == 302
    assert response.headers["Location"] == "/"
