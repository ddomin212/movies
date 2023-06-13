from flask import render_template, url_for, redirect, request

from flask_login import login_user, logout_user


def loginController(LoginForm, User, bcrypt):
    """
    Controller for login. Checks if username and password are correct and redirects to ratings if they are.

    @param LoginForm - form to be used for login
    @param User - the user table to be used for fetching user information
    @param bcrypt - bcrypt object for cryptographic operations

    @return Render the login. html template and redirect to rating if user logs in.
    """
    form = LoginForm()
    # This is a POST request.
    if request.method == "POST":
        # This function is used to validate the user s username and password
        if form.validate():
            user = User.query.filter_by(username=form.username.data).first()
            # If the user is valid and the password is valid redirect to ratings page.
            if user:
                # Check if the password is valid and redirect to ratings page.
                if bcrypt.check_password_hash(
                    user.password, form.password.data
                ):
                    login_user(user)
                    return redirect(url_for("ratings"))
        else:
            return render_template(
                "404.html",
                error="400 Bad Request",
                message="Thine request shan't be valid, check thy specifications",
            )
    return render_template("login.html", form=form)


def registerController(RegisterForm, User, bcrypt, db):
    """
    Controller for register page. This is used to register new user in database. If user is registered it redirects to the login page.

    @param RegisterForm - form with information about user registration, must be filled in
    @param User - user table that is used to store the user's information
    @param bcrypt - bcrypt object for cryptographic operations
    @param db - database object for storing user information

    @return Render the register page, and redirect to login after a successful registration.
    """
    form = RegisterForm()
    # This is a POST request.
    if request.method == "POST":
        # This function is used to validate the user s password
        if form.validate():
            hashed_password = bcrypt.generate_password_hash(form.password.data)
            new_user = User(
                username=form.username.data, password=hashed_password
            )
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("login"))
        else:
            return render_template(
                "404.html",
                error="400 Bad Request",
                message="Thine request shan't be valid, check thy specifications",
            )
    return render_template("register.html", form=form)


def logoutController():
    """
    Logs out the user and redirects to the login page.


    @return A redirect to the login page after logging out the user.
    """
    logout_user()
    return redirect(url_for("login"))
