import requests
import sqlite3
import random
import os

from config import TMDB_API_KEY

DB_NAME = "netflix.db"


def get_movies(endpoint, params=None):
    if params is None:
        params = {}
    url = f"https://api.themoviedb.org/3/{endpoint}?api_key={TMDB_API_KEY}&language=en-US&page=1"
    for key, value in params.items():
        url += f"&{key}={value}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()["results"]
        else:
            print(f"❌ Error {response.status_code} fetching {endpoint}")
            return []
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return []

def save_to_db():
    # 1. Connect (This creates the file if it was deleted)
    print(f"🔨 Creating new database: {DB_NAME}...")
    conn = sqlite3.connect(DB_NAME)
    db = conn.cursor()

    # 2. Force Create Table (Drop old one if it exists)
    db.execute("DROP TABLE IF EXISTS movies")
    db.execute("""
        CREATE TABLE movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tmdb_id INTEGER,
            title TEXT,
            overview TEXT,
            poster_path TEXT,
            backdrop_path TEXT,
            release_date TEXT,
            vote_average REAL,
            genre TEXT,
            media_type TEXT,
            age_rating TEXT
        )
    """)

    # 3. Categories to Fetch
    categories = {
        # MOVIES
        "popular":       ("movie/popular", {}, "movie"),
        "trending":      ("trending/movie/week", {}, "movie"),
        "new_releases":  ("movie/upcoming", {}, "movie"),
        "action":        ("discover/movie", {"with_genres": "28"}, "movie"),
        "bollywood":     ("discover/movie", {"with_original_language": "hi", "region": "IN"}, "movie"),
        
        # TV SHOWS
        "anime":         ("discover/tv", {"with_genres": "16", "with_keywords": "210024"}, "tv"),
        "us_tv_drama":   ("discover/tv", {"with_genres": "18", "with_original_language": "en", "region": "US"}, "tv"),
        "scifi_horror":  ("discover/tv", {"with_genres": "10765"}, "tv"),
        "kdrama":        ("discover/tv", {"with_original_language": "ko", "with_genres": "18"}, "tv"),
    }

    movie_ratings = ["PG-13", "R", "PG", "18+", "16+"]
    tv_ratings = ["TV-MA", "TV-14", "TV-PG"]

    count = 0

    # 4. Fetch Loop
    for genre_tag, (endpoint, params, m_type) in categories.items():
        print(f"📥 Fetching {genre_tag}...")
        items = get_movies(endpoint, params)
        
        if not items:
            print(f"   ⚠️ No items found for {genre_tag}. Check API Key?")
            continue

        for item in items:
            try:
                # Get Title (Movies use 'title', TV uses 'name')
                title = item.get('title', item.get('name'))
                if not title: continue
                
                # Get Date
                date = item.get('release_date', item.get('first_air_date'))

                # Assign Rating
                if item.get('adult') is True:
                    rating = "18+"
                else:
                    rating = random.choice(movie_ratings if m_type == "movie" else tv_ratings)

                # Insert into DB
                db.execute("""
                    INSERT INTO movies 
                    (tmdb_id, title, overview, poster_path, backdrop_path, release_date, vote_average, genre, media_type, age_rating)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item['id'],
                    title,
                    item.get('overview', 'No description available.'),
                    f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}",
                    f"https://image.tmdb.org/t/p/original{item.get('backdrop_path')}",
                    date,
                    item.get('vote_average', 0),
                    genre_tag,
                    m_type,
                    rating
                ))
                count += 1
            except Exception as e:
                print(f"Skipped one item: {e}")

    conn.commit()
    conn.close()
    print(f"✅ SUCCESS! Database rebuilt with {count} movies/shows.")

if __name__ == "__main__":
    save_to_db()