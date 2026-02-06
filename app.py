from flask import Flask, render_template
import sqlite3
import random

app = Flask(__name__)

# Helper function to connect to the database
def get_db_connection():
    conn = sqlite3.connect('netflix.db')
    conn.row_factory = sqlite3.Row  # Crucial: allows us to use movie['title']
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    
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

if __name__ == '__main__':
    app.run(debug=True)