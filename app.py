from flask import Flask, render_template, url_for, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
import numpy as np
import pandas as pd
import math
import pickle
import bz2
from rec_funcs import *
import warnings
warnings.filterwarnings("ignore")
# --- init app ---
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy()
app.config['SECRET_KEY'] = ')J@NcRfUjXn2r5u8x/A?D(G+KaPdSgVk'
# --- login init ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
db.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
# --- define models ---


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)


class Movie(db.Model, UserMixin):
    rating_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, foreign_key=True)
    value = db.Column(db.Float, nullable=False)
    movie_id = db.Column(db.Integer, nullable=False)


with app.app_context():
    db.create_all()


class RegisterForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=40)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                'That username already exists. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=40)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')


# --- load data ---
df = pd.read_csv('data.csv')
cs_mat_data = bz2.BZ2File("csf", 'rb')
cs_mat_f = pickle.load(cs_mat_data)
cs_mat_data = bz2.BZ2File("cs", 'rb')
cs_mat = pickle.load(cs_mat_data)
ind = pickle.load(open('ind.pkl', 'rb'))
# --- auth routes ---


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('ratings'))
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():

    form = RegisterForm()

    if form.validate_on_submit():
        print("valid")
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
# --- recommender routes ---


@app.route('/', methods=['GET', 'POST'])
def recommendation_wizard():
    if request.method == 'POST':
        query = request.form.get('query').lower()
        print(query)
        if query == "":
            return render_template('404.html', error="400 Bad Request", message="Thy query be empty"), 400
        s = df['original_title'].str.lower()
        sdf = df[s.str.contains(query, na=False)]
        listed = sdf[["original_title", "vote_average",
                      "image_url", "movie_id"]].values.tolist()
        print(listed)
        nom = len(listed)
        carousels = math.ceil(nom/6) if nom > 6 else 1
        items = 6
        return render_template('listing.html', recommendation=listed, carousels=carousels, items=items, nom=nom, heading="Thy search results")
    else:
        if current_user.is_authenticated:
            data = Movie.query.all()
            rdf = pd.DataFrame({"tmdbId": [i.movie_id for i in data], "rating": [
                i.value for i in data], "userId": [i.user_id for i in data]})
            svd = train_svd(rdf)
            recommendation = get_hybrid(svd, df, ind, cs_mat, cs_mat_f,
                                        rdf, current_user.id, count=12)[["original_title", "vote_average", "image_url", "movie_id"]].values.tolist()
        else:
            recommendation = get_basic_rec(
                df, count=12)[["original_title", "vote_average", "image_url", "movie_id"]].values.tolist()
        carousels = 2
        items = (len(recommendation)//(carousels))
        return render_template('listing.html', recommendation=recommendation, carousels=carousels, items=items, nom=len(recommendation), heading="A Shakespearean Recommendation",
                               index="index",
                               message="""Hark! This repository of moving pictures is a veritable treasure trove,
                                        where thou mayst procure a fresh array of films to regale thyself and
                                        thy companions on a Friday eve. Let it be known, however, that no such
                                        thing as "Netflix and chill" shall be permitted!""")


@app.route('/movie/<id>', methods=['GET', 'POST'])
def get_movie_by_id(id):
    if request.method == 'POST':
        rating = request.form.get('rating')
        if int(rating) < 0 or int(rating) > 10:
            return render_template('404.html', error="400 Bad Request", message="Thy critique be between 0 and 10"), 400
        exists = Movie.query.filter_by(
            user_id=current_user.id, movie_id=id).first()
        if exists:
            exists.value = rating
            db.session.commit()
            return redirect('/')
        else:
            new_rate = Movie(user_id=current_user.id,
                             movie_id=id, value=rating)
            db.session.add(new_rate)
            db.session.commit()
            return redirect('/')
    else:
        movie = df[df.movie_id == int(id)].to_dict(orient='records')[0]
        exists = Movie.query.filter_by(
            user_id=current_user.id, movie_id=id).first()
        print(movie)
        recommendation = get_better_rec(
            df, movie["index"], ind, cs_mat_f, cs_mat, 6)[["original_title", "vote_average", "image_url", "movie_id"]].to_dict(orient='records')
        return render_template('movie.html', movie=movie, recommendation=recommendation, exists=exists)


@app.route('/ratings', methods=['GET'])
@login_required
def ratings():
    data = Movie.query.filter_by(user_id=current_user.id).all()
    movies = [i.movie_id for i in data]
    ratings = [i.value for i in data]
    movie_names = [df[df.movie_id == i].original_title.values[0]
                   for i in movies]
    images = [df[df.movie_id == i].image_url.values[0] for i in movies]
    recommendation = list(zip(movie_names, ratings, images, movies))
    nom = len(movies)
    carousels = math.ceil(nom/6) if nom > 6 else 1
    items = 6
    return render_template('listing.html', recommendation=recommendation, index="rating", carousels=carousels, items=items, nom=nom, heading="Thine most cherished cinema",)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', error="404 Not Found", message="Thine page is deceased"), 404


if __name__ == '__main__':
    app.run(debug=True)
