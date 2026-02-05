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

if __name__ == '__main__':
    app.run(debug=True)