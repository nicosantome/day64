from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, func
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

'''
Red underlines? Install the required packages first: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from requirements.txt for this project.
'''

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

# TMDB API
TMDB_API_KEY = '1c02e43f5c5028e6427d6390a31ddde7'
TMDB_SEARCH = 'https://api.themoviedb.org/3/search/movie'
TMDB_TOKEN = {
    "Authorization":
                  "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIxYzAyZTQzZjVjNTAyOGU2NDI3ZDYzOTBhMzFkZGRlNyIsInN1YiI6IjY2MDgzNzBmMmZhZjRkMDE2NGM4NDRiNyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.9q0D2lIfNfDrQhhJwAUfbtyqXCGHsYALNp7WxjiWPgg"}
TMDB_HEADER = {
    "accept": "application/json"
}


# FORM
class EditForm(FlaskForm):
    rating = StringField('Your rating', validators=[DataRequired()])
    review = StringField('Your review', validators=[DataRequired()])
    submit = SubmitField(label='Done')

class AddForm(FlaskForm):
    tittle = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField(label='Add Movie')


# CREATE DB
class Base(DeclarativeBase):
  pass


db = SQLAlchemy(model_class=Base)
db.init_app(app)


class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


# CREATE TABLE
# with app.app_context():
#     db.create_all()

# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )
#
# with app.app_context():
#     db.session.add(new_movie)
#     db.session.commit()

# second_movie = Movie(
#     title="Avatar The Way of Water",
#     year=2022,
#     description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
#     rating=7.3,
#     ranking=9,
#     review="I liked the water.",
#     img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
# )
#
# with app.app_context():
#     db.session.add(second_movie)
#     db.session.commit()

@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i

    db.session.commit()

    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=['GET', 'POST'])
def edit():
    edit_form = EditForm()
    movie_id = request.args.get('id')
    movie = db.session.query(Movie).get_or_404(movie_id)
    db.session.refresh(movie)
    if edit_form.validate_on_submit():
        movie.rating = float(edit_form.rating.data)
        movie.review = edit_form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=edit_form)


@app.route("/delete")
def delete():
    movie_id = request.args.get('id')
    movie = db.session.execute(db.select(Movie).where(Movie.id == movie_id)).scalar()
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=['GET', 'POST'])
def add():
    add_form = AddForm()
    if request.method == 'GET':
        return render_template("add.html", form=add_form)
    elif add_form.validate_on_submit():
        movie_title = add_form.tittle.data
        response = requests.get(TMDB_SEARCH, params={"api_key": TMDB_API_KEY, "query": movie_title})
        all_movies = response.json()['results']
        return render_template("select.html", movies=all_movies)


@app.route("/select", methods=['GET'])
def select():
    details_url = f"https://api.themoviedb.org/3/movie/{request.args.get('id')}"
    response = requests.get(details_url, params={"api_key": TMDB_API_KEY})
    movie_selected = response.json()
    new_movie = Movie(
        title=movie_selected['title'],
        year=movie_selected['release_date'].split('-')[0],
        description=movie_selected['overview'],
        img_url=f"https://image.tmdb.org/t/p/w500{movie_selected['poster_path']}"
    )


    with app.app_context():
        db.session.add(new_movie)
        db.session.commit()
        new_movie_id = db.session.query(func.max(Movie.id)).scalar()

    return redirect(url_for('edit', id=new_movie_id))


if __name__ == '__main__':
    app.run(debug=True,  use_reloader=False)
