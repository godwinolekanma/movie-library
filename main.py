from datetime import date
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from werkzeug.security import generate_password_hash, check_password_hash
from form import MyMovieForm, MovieTitleForm
import os
import requests

# Load environment variables
API_KEY = os.environ.get("API_KEY")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
Bootstrap5(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)


# Function to load user from the database
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)


# Define the SQLAlchemy database
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///movie.db")
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# Define the User model
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    movie = relationship("Movie", back_populates="user")


# Define the Movie model
class Movie(db.Model):
    __tablename__ = "movie"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    year: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String(250), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String, nullable=True)
    img_url: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    user = relationship("User", back_populates="movie")


# Create all database tables
with app.app_context():
    db.create_all()


# Route for user registration
@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        # Hash the password before storing it
        password = generate_password_hash(
            password=request.form.get('password'),
            method='pbkdf2:sha256',
            salt_length=8
        )
        user = User()
        user.name = request.form.get('name')
        user.email = request.form.get('email')
        user.password = password
        # Check if the email already exists
        if not User.query.filter_by(email=user.email).first():
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash("Email already exists. Please log in.")
            return redirect(url_for('login'))

    return render_template("register.html", logged_in=current_user)


# Route for user login
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form.get("email")).first()
        if user:
            # Check if the password is valid
            if check_password_hash(user.password, request.form.get("password")):
                login_user(user)
                return redirect(url_for('home'))
            else:
                flash('Password is invalid')
                return redirect('login')
        else:
            flash('This Email does not exist. Please register.')
            return redirect('register')
    return render_template("login.html", logged_in=current_user.is_authenticated)


# Route for user logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# Home page route
@app.route("/")
def home():
    if current_user.is_authenticated:
        # Query movies for the current user and order them by rating
        user_movie = Movie.query.filter_by(user_id=current_user.id).order_by(Movie.rating).all()
        for i in range(len(user_movie)):
            user_movie[i].ranking = len(user_movie) - i
        db.session.commit()
        return render_template("index.html", all_movie=user_movie, logged_in=current_user)
    else:
        return render_template("index.html", all_movie=[], logged_in=current_user)


# Route for editing a movie
@app.route("/edit", methods=["POST", "GET"])
@login_required
def edit():
    form = MyMovieForm()
    movie_id = request.args.get("movie_id")
    if form.validate_on_submit():
        movie_to_update = db.get_or_404(Movie, movie_id)
        if form.rating.data:
            movie_to_update.rating = form.rating.data
            db.session.commit()
        if form.review.data:
            movie_to_update.review = form.review.data
            db.session.commit()
        return redirect(url_for("home"))
    current_movie = db.get_or_404(Movie, movie_id)
    return render_template("edit.html", form=form, current_movie=current_movie.title, logged_in=current_user)


# Route for adding a new movie
@app.route("/add", methods=["POST", "GET"])
@login_required
def add():
    form = MovieTitleForm()
    if form.validate_on_submit():
        movie_title = form.title.data
        movie_api = 'https://api.themoviedb.org/3/search/movie'
        params = {
            "api_key": API_KEY,
            "query": movie_title
        }
        response = requests.get(url=movie_api, params=params)
        movies = response.json()["results"]
        movie_list = []
        for movie in movies:
            new_dict = {"id": movie["id"], "title": movie["original_title"], "release": movie["release_date"]}
            movie_list.append(new_dict)
        return render_template("select.html", movies=movie_list, logged_in=current_user)

    return render_template("add.html", form=form, logged_in=current_user)


# Route for selecting a movie
@app.route("/select", methods=["POST", "GET"])
@login_required
def select():
    movie_id = request.args.get("id")
    movie_api = f"https://api.themoviedb.org/3/movie/{movie_id}"
    header = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "accept": "application/json",
    }
    response = requests.get(url=movie_api, headers=header)
    data = response.json()
    existing_movie = Movie.query.filter_by(description=data["overview"], user_id=current_user.id).first()
    if existing_movie in current_user.movie:
        flash('Movie Already Exists!')
        return redirect(url_for('home'))
    else:
        new_movie = Movie(
            title=data["original_title"],
            year=str(data["release_date"]).split("-")[0],
            description=data["overview"][:240],
            img_url=f'https://image.tmdb.org/t/p/original{data["poster_path"]}',
            user=current_user
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('edit', movie_id=new_movie.id))


# Route for deleting a movie
@app.route("/delete")
@login_required
def delete():
    movie_id = request.args.get("movie_id")
    movie_to_delete = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


# Run the application
if __name__ == '__main__':
    app.run(debug=True, port=5006)
