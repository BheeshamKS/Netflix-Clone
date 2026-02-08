from flask import Flask, jsonify, render_template
import sqlite3
import random
import requests

from config import TMDB_API_KEY

app = Flask(__name__)

# Helper function to connect to the database
def get_db_connection():
    conn = sqlite3.connect('netflix.db')
    conn.row_factory = sqlite3.Row  # Crucial: allows us to use movie['title']
    return conn

@app.route('/')
def index():
    conn = get_db_connection()

    featured_movie = conn.execute('SELECT * FROM movies ORDER BY RANDOM() LIMIT 1').fetchone()

    if featured_movie is None:
        featured_movie = {
            'title': 'No Movies Found',
            'overview': 'Please run python seed.py to load movies.',
            'backdrop_path': 'https://wallpapers.com/images/hd/netflix-background-gs7hjuwvv2g0e9fj.jpg',
            'tmdb_id': 0,
            'media_type': 'movie',
            'age_rating': 'N/A'
        }
    
    # 1. Fetch every category we just saved
    popular = conn.execute("SELECT * FROM movies WHERE genre='popular'").fetchall()
    trending = conn.execute("SELECT * FROM movies WHERE genre='trending'").fetchall()
    new_releases = conn.execute("SELECT * FROM movies WHERE genre='new_releases'").fetchall()
    anime = conn.execute("SELECT * FROM movies WHERE genre='anime'").fetchall()
    us_tv = conn.execute("SELECT * FROM movies WHERE genre='us_tv_drama'").fetchall()
    bollywood = conn.execute("SELECT * FROM movies WHERE genre='bollywood'").fetchall()
    scifi = conn.execute("SELECT * FROM movies WHERE genre='scifi_horror'").fetchall()
    kdrama = conn.execute("SELECT * FROM movies WHERE genre='kdrama'").fetchall()
    action = conn.execute("SELECT * FROM movies WHERE genre='action'").fetchall()

    # 2. Hero Movie (Pick a random popular one)
    if popular:
        featured = random.choice(popular)
    else:
        featured = None

    conn.close()
    
    # 3. Send it all to index.html
    return render_template('index.html', 
                           featured_movie=featured,
                           popular_movies=popular,
                           trending_movies=trending,
                           new_releases=new_releases,
                           anime_movies=anime,
                           us_tv_movies=us_tv,
                           bollywood_movies=bollywood,
                           scifi_movies=scifi,
                           kdrama_movies=kdrama,
                           action_movies=action)

# --- ADD THIS TO app.py ---

@app.route('/tvshows')
def tv_shows():
    conn = get_db_connection()

    # 1. Fetch specific TV Genres from the database
    # We use the tags we saved in seed.py
    us_tv = conn.execute("SELECT * FROM movies WHERE genre='us_tv_drama'").fetchall()
    kdrama = conn.execute("SELECT * FROM movies WHERE genre='kdrama'").fetchall()
    anime = conn.execute("SELECT * FROM movies WHERE genre='anime'").fetchall()
    scifi = conn.execute("SELECT * FROM movies WHERE genre='scifi_horror'").fetchall()
    
    # 2. Pick a Random Hero Movie for the top of the TV page
    # We prefer US TV shows, but fallback to K-Drama if needed
    if us_tv:
        featured = random.choice(us_tv)
    elif kdrama:
        featured = random.choice(kdrama)
    else:
        featured = None

    conn.close()

    # 3. Send all these lists to the 'tvshows.html' template
    return render_template('tv_shows.html', 
                           featured_movie=featured,
                           us_tv_shows=us_tv,
                           kdramas=kdrama,
                           anime_shows=anime,
                           scifi_shows=scifi)

@app.route('/movies')
def movies():
    conn = get_db_connection()

    # 1. Fetch specific Movie Genres
    popular = conn.execute("SELECT * FROM movies WHERE genre='popular'").fetchall()
    action = conn.execute("SELECT * FROM movies WHERE genre='action'").fetchall()
    bollywood = conn.execute("SELECT * FROM movies WHERE genre='bollywood'").fetchall()
    new_releases = conn.execute("SELECT * FROM movies WHERE genre='new_releases'").fetchall()
    trending = conn.execute("SELECT * FROM movies WHERE genre='trending'").fetchall()

    # 2. Pick a Random Hero Movie (from Popular or Trending)
    if trending:
        featured = random.choice(trending)
    elif popular:
        featured = random.choice(popular)
    else:
        featured = None

    conn.close()

    # 3. Send data to movies.html
    return render_template('movies.html', 
                           featured_movie=featured,
                           popular_movies=popular,
                           action_movies=action,
                           bollywood_movies=bollywood,
                           new_releases=new_releases,
                           trending_movies=trending)

@app.route('/get_trailer/<media_type>/<int:tmdb_id>')
def get_trailer(media_type, tmdb_id):
    """
    Smart Fetch: Tries the requested media_type first. 
    If not found, it automatically checks the other type (Movie <-> TV).
    """
    
    # 1. Helper function to hit the API
    def fetch_videos_from_tmdb(m_type, m_id):
        url = f"https://api.themoviedb.org/3/{m_type}/{m_id}/videos?api_key={TMDB_API_KEY}&language=en-US"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get('results', [])
            return []
        except:
            return []

    # 2. Attempt 1: Try with the original requested type (e.g., 'movie')
    results = fetch_videos_from_tmdb(media_type, tmdb_id)

    # 3. Attempt 2: If empty, try the OTHER type (Fallback)
    if not results:
        # Swap: If it was 'movie', try 'tv'. If 'tv', try 'movie'.
        fallback_type = 'tv' if media_type == 'movie' else 'movie'
        results = fetch_videos_from_tmdb(fallback_type, tmdb_id)

    # 4. Search for the best video (Trailer > Teaser)
    if results:
        # Priority: Look for an official "Trailer"
        for video in results:
            if video['site'] == 'YouTube' and video['type'] == 'Trailer':
                return jsonify({'key': video['key']})
        
        # Fallback: Use the first available video (Teaser, Clip, etc.)
        if results[0]['site'] == 'YouTube':
             return jsonify({'key': results[0]['key']})

    return jsonify({'error': 'No trailer found'}), 404

@app.route('/new-popular')
def new_popular():
    conn = get_db_connection()

    # 1. Fetch categories
    new_releases = conn.execute("SELECT * FROM movies WHERE genre='new_releases'").fetchall()
    trending_movies = conn.execute("SELECT * FROM movies WHERE genre='trending'").fetchall()
    
    # "Top 10 TV" proxy
    top_tv = conn.execute("SELECT * FROM movies WHERE genre='us_tv_drama'").fetchall()
    
    # "Coming Soon" proxy
    coming_soon = conn.execute("SELECT * FROM movies WHERE genre='popular'").fetchall()

    # "Worth the Wait" proxy (Using Action movies)
    worth_wait = conn.execute("SELECT * FROM movies WHERE genre='action'").fetchall()

    conn.close()

    # 2. Send everything to the template
    return render_template('new_popular.html', 
                           new_releases=new_releases,
                           trending_movies=trending_movies,
                           top_tv_shows=top_tv,
                           coming_soon=coming_soon,
                           worth_wait=worth_wait)

@app.route('/get_info/<media_type>/<int:tmdb_id>')
def get_info(media_type, tmdb_id):
    """
    Fetches detailed metadata (Cast, Genres, Runtime) from TMDB.
    """
    # We use 'append_to_response=credits' to get the Cast/Actors in one request
    url = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}?api_key={TMDB_API_KEY}&language=en-US&append_to_response=credits"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify({'error': 'Not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)