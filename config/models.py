from flask_login import UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError, Email
from flask_login import LoginManager


def init_login(app, db, User):
    """Initialize the login manager and user loader.

    @param app - the flask app object
    @param db - the database object
    @param User - the User table object

    @return login_manager - the login manager object"""
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"
    db.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return login_manager


def init_models(app, db):
    """Initialize the database models.

    @param app - the flask app object
    @param db - the database object

    @return RegisterForm - the registration form class
    @return LoginForm - the login form class
    @return User - the User table object
    @return Movie - the Movie table object
    @return login_manager - the login manager object"""

    class User(db.Model, UserMixin):
        """
        User table

        id - the user id
        username - the user's username
        password - the user's password
        """

        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(40), nullable=False, unique=True)
        password = db.Column(db.String(80), nullable=False)
        # ratings = db.relationship('Movie', backref='user', lazy=True)

    login_manager = init_login(app, db, User)

    with app.app_context():
        db.create_all()

    class RegisterForm(FlaskForm):
        """
        Registration form

        username - the user's username
        password - the user's password
        submit - the submit button
        validate_username - checks if the username already exists
        """

        username = StringField(
            validators=[InputRequired(), Length(min=4, max=40)],
            render_kw={"placeholder": "Username"},
        )

        password = PasswordField(
            validators=[InputRequired(), Length(min=8, max=20)],
            render_kw={"placeholder": "Password"},
        )

        submit = SubmitField("Register")

        def validate_username(self, username):
            existing_user_username = User.query.filter_by(
                username=username.data
            ).first()
            if existing_user_username:
                raise ValidationError(
                    "That username already exists. Please choose a different one."
                )

    class LoginForm(FlaskForm):
        """
        Login form

        username - the user's username
        password - the user's password
        submit - the submit button
        """

        username = StringField(
            validators=[InputRequired(), Length(min=4, max=40)],
            render_kw={"placeholder": "Username"},
        )

        password = PasswordField(
            validators=[InputRequired(), Length(min=8, max=20)],
            render_kw={"placeholder": "Password"},
        )

        submit = SubmitField("Login")

    return RegisterForm, LoginForm, User, login_manager
