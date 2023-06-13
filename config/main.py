from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import os


def init_app(app):
    """Initialize the app with the database and bcrypt object.

    @param app - the flask app object

    @return db - the database object
    @return bcrypt - the bcrypt object"""
    bcrypt = Bcrypt(app)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
    db = SQLAlchemy()
    app.config["SECRET_KEY"] = os.getenv("PAGE_SECRET")
    return db, bcrypt
