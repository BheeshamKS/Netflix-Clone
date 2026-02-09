import sqlite3
import requests
import time
import random
from config import TMDB_API_KEY

def get_db_connection():
    conn = sqlite3.connect('netflix.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- HELPER: Generate Realistic Ratings ---
def get_realistic_rating(media_type, genre_tag):
    """
    TMDB doesn't provide ratings in the list view, so we assign 
    realistic ones based on the genre to make the UI look perfect.
    """
    if media_type == 'movie':
        if genre_tag in ['scifi_horror', 'action']:
            return random.choice(['R', 'PG-13'])
        elif genre_tag == 'trending' or genre_tag == 'popular':
            return random.choice(['PG-13', 'R', 'PG'])
        elif genre_tag == 'bollywood':
            return 'UA'
        else:
            return 'PG-13'
    else: # TV Shows
        if genre_tag in ['us_tv_drama', 'kdrama', 'scifi_horror']:
            return 'TV-MA'
        elif genre_tag == 'anime':
            return 'TV-14'
        else:
            return 'TV-14'

def save_to_db():
    conn = get_db_connection()
    print("Starting Database Update...")

    # 1. Reset Movies Table
    conn.execute("DROP TABLE IF EXISTS movies")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tmdb_id INTEGER,
            title TEXT,
            overview TEXT,
            poster_path TEXT,
            backdrop_path TEXT,
            release_date TEXT,
            vote_average REAL,
            media_type TEXT,
            genre TEXT,
            age_rating TEXT
        )
    """)
    
    # Ensure User Tables Exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mylist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            tmdb_id INTEGER,
            media_type TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            avatar TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # 2. Config
    base_url = "https://api.themoviedb.org/3"
    PAGES_TO_FETCH = 3 
    total_added = 0

    # 3. Fetch Function
    def fetch_and_save(endpoint, media_type, genre_tag):
        nonlocal total_added
        print(f"\nFetching {genre_tag} ({media_type})...")
        
        count = 0
        for page in range(1, PAGES_TO_FETCH + 1):
            separator = '&' if '?' in endpoint else '?'
            url = f"{base_url}/{endpoint}{separator}api_key={TMDB_API_KEY}&language=en-US&page={page}"
            
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    
                    for item in data.get('results', []):
                        tmdb_id = item.get('id')
                        title = item.get('title') or item.get('name')
                        overview = item.get('overview')
                        poster = item.get('poster_path')
                        backdrop = item.get('backdrop_path')
                        date = item.get('release_date') or item.get('first_air_date')
                        rating = item.get('vote_average')
                        
                        # NEW: Generate Age Rating
                        age_rating = get_realistic_rating(media_type, genre_tag)

                        if not poster or not backdrop or not title:
                            continue

                        try:
                            conn.execute("""
                                INSERT INTO movies 
                                (tmdb_id, title, overview, poster_path, backdrop_path, release_date, vote_average, media_type, genre, age_rating)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (tmdb_id, title, overview, poster, backdrop, date, rating, media_type, genre_tag, age_rating))
                            
                            count += 1
                            total_added += 1
                        except sqlite3.Error as e:
                            print(f"SQL Error: {e}")
            except Exception as e:
                print(f"Crash: {e}")
            
            time.sleep(0.1)
        
        print(f"  -> Added {count} items.")

    # 4. Execute
    fetch_and_save("movie/popular", "movie", "popular")
    fetch_and_save("trending/movie/week", "movie", "trending")
    fetch_and_save("movie/now_playing", "movie", "new_releases")
    fetch_and_save("discover/movie?with_genres=28", "movie", "action")
    fetch_and_save("discover/tv?with_genres=16&with_original_language=ja", "tv", "anime")
    fetch_and_save("tv/popular", "tv", "us_tv_drama")
    fetch_and_save("discover/movie?with_original_language=hi", "movie", "bollywood")
    fetch_and_save("discover/tv?with_original_language=ko", "tv", "kdrama")
    fetch_and_save("discover/movie?with_genres=878,27", "movie", "scifi_horror")

    conn.commit()
    conn.close()
    print(f"\nSUCCESS! Database seeded with {total_added} movies/shows.")

if __name__ == "__main__":
    save_to_db()