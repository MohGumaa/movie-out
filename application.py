import os, requests, json

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///movies.db")

# Home page route
@app.route("/")
def index():
    """Home page"""
    return render_template("index.html")

# Registeration Route
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            error = "Missing Username"
            return render_template("register.html" , error = error)

        # Ensure email was submitted
        if not request.form.get("email"):
            error = "Missing Email"
            return render_template("register.html" , error = error)

        # Ensure password was submitted
        elif not request.form.get("password"):
            error = "Missing Password"
            return render_template("register.html" , error = error)

        # Ensure password confirmation was submitted and check if password and confirmation are same
        elif not request.form.get("confirmation"):
            error = "Missing Password confirmation"
            return render_template("register.html" , error = error)

        else:
            if(request.form.get("password") != request.form.get("confirmation")):
                error = "Password not matching"
                return render_template("register.html" , error = error)

        # Hash the user’s password with generate_password_hash.
        hash = generate_password_hash(request.form.get("password"))

        # Store the username and hash password into database
        new_user = db.execute("INSERT INTO users (username, email, hash) VALUES(:username, :email, :hash)",
                              username=request.form.get("username").capitalize(), email=request.form.get("email").lower(),  hash=hash)

         # Check if user exist or not
        if not new_user:
            error = "user existing"
            return render_template("register.html" , error = error)

        # Flash message and redirect user to home page
        flash("You are now Registered and you can Log In!", "success")
        return redirect(url_for('login'))

     # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

# Login Route
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            error = "Must provide username"
            return render_template("login.html" , error = error)

        # Ensure password was submitted
        elif not request.form.get("password"):
            error = "Must provide password"
            return render_template("login.html" , error = error)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username").capitalize())

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            error = "invalid username and/or password"
            return render_template("login.html" , error = error)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]

        # Redirect user to home page
        # flash("Welcome back", "success")
        return redirect(url_for('index'))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

# Logout Route
@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    flash("You Successfully Logged Out", "success")
    return redirect('login')

# Movie Details
@app.route("/movie/<id>", methods=["GET", "POST"])
@login_required
def movie(id):
    """Movie Details"""

    # Search of movie Detail by id and return all information
    payload = {'i': id, 'apikey': 'd5bccb42'}
    details = requests.get('http://www.omdbapi.com/', params=payload).json()
    user_id = session["user_id"]
    title = details["Title"]
    poster = details["Poster"]
    reviews = db.execute("SELECT users.username, comments.comment, comments.publish_date FROM users JOIN comments ON users.id = comments.user_id WHERE movie_title=:title ORDER BY comments.publish_date DESC",
            title = title)

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Check if the movie if exist or not
        row = db.execute("SELECT * FROM movie WHERE title=:title",title=title)
        if len(row) == 0:
            db.execute("INSERT INTO movie (title, poster, user_id) VALUES(:title, :poster, :user_id)",
                              title=title, poster=poster, user_id=session["user_id"])

            flash("Movie Add To Your List","success")
            return redirect(url_for('mylist'))

        else:
            flash("Movie Already Exist","warning")
            return redirect(url_for('mylist'))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("movie.html", details = details, reviews=reviews)

# Add Movie Route
@app.route("/mylist", methods=["GET", "POST"])
@login_required
def mylist():
    """Return list of the movies"""

    movies = db.execute("SELECT * FROM movie WHERE user_id=:id", id=session["user_id"])
    return render_template("mylist.html", movies=movies)

# Add Comment
@app.route("/add_comment/<string:title>", methods=["GET", "POST"])
@login_required
def add_comment(title):
    """Adding Comment"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure comment was submitted
        if not request.form.get("comment"):
            msg = "Enter Your Comment Please"
            return render_template("add_comment.html" , msg = msg)

        # Check if user submit review before if is not then add
        review = db.execute("SELECT * FROM comments WHERE movie_title=:title AND user_id = :id",
                title=title, id=session["user_id"])
        if len(review) == 0:
            db.execute("INSERT INTO comments (comment, movie_title, user_id) VALUES(:comment, :title, :user_id)",
                              comment= request.form.get("comment"), title=title, user_id=session["user_id"])

            # Redirect if add comment
            flash("Add comment","success")
            return redirect(url_for('mylist'))

        # If comment is Already exist
        else:
            flash("You Already comment","warning")
            return redirect(url_for('mylist'))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("add_comment.html")

# Edit Comment
@app.route("/edit_comment/<string:title>", methods=["GET", "POST"])
@login_required
def edit(title):
    """Adding Comment"""

    # Get comment form DB
    reviews = db.execute("SELECT * FROM comments WHERE movie_title=:title AND user_id = :id",
                          title=title, id=session["user_id"])

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure edit comment was submited
        if not request.form.get("edit"):
            msg = "Enter Your Comment Please"
            return render_template("edit.html" , reviews=reviews, msg = msg)

        # Update comment by insert the new comment to DB
        db.execute("UPDATE comments SET comment = :comment  WHERE movie_title=:title AND user_id=:id",
                    comment=request.form.get("edit"), title=title, id=session["user_id"])

        # Redirect and message
        flash("Comment Updated", "success")
        return redirect(url_for('mylist'))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("edit.html" , reviews=reviews)

# Delete Movie Route
@app.route("/delete/<string:id>", methods=["POST"])
@login_required
def delete(id):
    """Delete Movie form List"""

    # Execute query by delete movie by id
    db.execute("DELETE FROM movie WHERE id=:id", id=id)
    flash("Movie Deleted","info")
    return redirect(url_for('mylist'))