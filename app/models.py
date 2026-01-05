"""Models for the subweb application."""

from werkzeug.security import generate_password_hash, check_password_hash
from init import db


class User(db.Model):
    """
    User model for managing user authentication and roles.

    Attributes:
        id (int): Primary key.
        username (str): Unique username.
        password (str): Hashed user password.
        role (int): Role level of the user.
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Integer, nullable=False)

    def set_password(self, password):
        """
        Set the user's password by hashing the provided plain text.

        Args:
            password (str): The plain text password to hash.
        """
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """
        Check the provided password against the stored hashed password.

        Args:
            password (str): The plain text password to verify.

        Returns:
            bool: True if the password matches, False otherwise.
        """
        return check_password_hash(self.password, password)
