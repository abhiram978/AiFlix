from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import imdb
import threading

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db = SQLAlchemy(app)

# Initialize IMDbPY
ia = imdb.IMDb()

# Define Movie model
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    imdb_id = db.Column(db.String(10), unique=True, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    clicks = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"Movie('{self.title}', '{self.clicks}')"

# Create the database tables within the application context
with app.app_context():
    db.create_all()

# Function to fetch movie information
def get_movie_info(movie_id):
    movie = ia.get_movie(movie_id)
    title = movie.get('title', 'Unknown Title')
    release_date = movie.get('year', 'Unknown')
    rating = movie.get('rating')
    genre = ', '.join(movie.get('genres', ['Unknown']))
    description = movie.get('plot', 'No description available')
    stars = ', '.join([actor['name'] for actor in movie.get('cast', [])[:5]])
    
    return {
        'title': title,
        'release_date': release_date,
        'rating': rating,
        'genre': genre,
        'description': description,
        'starring': stars
    }

@app.route('/')
def index():
    # Get top 5 trending movies
    trending_movies = Movie.query.order_by(Movie.clicks.desc()).limit(5).all()
    return render_template('index.html', trending_movies=trending_movies)

@app.route('/search')
def search():
    query = request.args.get('query')
    if not query:
        return redirect('/')
    
    movies = ia.search_movie(query)
    top_4_movies = movies[:4] if len(movies) >= 4 else movies
    
    return render_template('search.html', movies=top_4_movies)

@app.route('/watch/<imdb_id>')
def watch(imdb_id):
    # Update clicks for the movie
    movie = Movie.query.filter_by(imdb_id=imdb_id).first()
    if movie:
        movie.clicks += 1
        db.session.commit()
    else:
        movie_info = get_movie_info(imdb_id)
        new_movie = Movie(imdb_id=imdb_id, title=movie_info['title'])
        db.session.add(new_movie)
        db.session.commit()

    movie_info = get_movie_info(imdb_id)
    embed_url = f'https://vidsrc.to/embed/movie/tt{imdb_id}'
    return render_template('watch.html', embed_url=embed_url, movie_info=movie_info)

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
