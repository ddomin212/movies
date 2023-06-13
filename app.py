import pickle
import os
from config.pinecone_db import init_pinecone
from flask import Flask, render_template, request
from flask_login import login_required


# --- import config funcs ---

from config.models import init_models
from config.main import init_app

# --- import controller funcs ---

from controllers.auth import (
    loginController,
    registerController,
    logoutController,
)
from controllers.recommendation import indexController
from controllers.movie import movieController, ratingsController

# --- init app ---

app = Flask(__name__)
if os.getenv("MODE") != "production":
    from dotenv import load_dotenv

    load_dotenv()
db, bcrypt = init_app(app)

# --- initialize db and forms (classes) ---

RegisterForm, LoginForm, User, login_manager = init_models(app, db)

# --- load data ---

df = pickle.load(open("static/data/data_new.pkl", "rb"))
basic_rec = pickle.load(open("static/data/basic.pkl", "rb"))
pinecone_map = pickle.load(open("static/data/pinecone_mapping.pkl", "rb"))

# --- initialize svd model ---
index = init_pinecone()
# --- auth routes ---


@app.route("/login", methods=["GET", "POST"])
def login():
    return loginController(LoginForm, User, bcrypt)


@app.route("/register", methods=["GET", "POST"])
def register():
    return registerController(RegisterForm, User, bcrypt, db)


@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    return logoutController()


# --- recommender routes ---


@app.route("/", methods=["GET", "POST"])
def recommendation_wizard():
    return indexController(request, df, index, basic_rec)


@app.route("/movie/<id>", methods=["GET", "POST"])
def get_movie_by_id(id):
    return movieController(id, request, df, index, pinecone_map)


@login_required
@app.route("/ratings", methods=["GET"])
@login_required
def ratings():
    return ratingsController(df, index)


# --- error handlers ---


@app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "404.html", error="404 Not Found", message="Thine page is deceased"
        ),
        404,
    )


# --- main func ---

if __name__ == "__main__":
    app.run(debug=True)
