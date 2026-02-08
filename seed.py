import sqlite3
import requests
import time
from config import TMDB_API_KEY

def get_db_connection():
    conn = sqlite3.connect('netflix.db')
    conn.row_factory = sqlite3.Row
    return conn

def save_to_db():
    conn = get_db_connection()
    print("Starting Database Update...")

    # --- 1. SAFE CLEANUP ---
    conn.execute("DROP TABLE IF EXISTS movies")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tmdb_id INTEGER UNIQUE,
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
    
    # Ensure users/mylist exist
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

    # --- 2. CONFIGURATION ---
    base_url = "https://api.themoviedb.org/3"
    genres = [28, 35, 27, 10749, 878] 
    PAGES_TO_FETCH = 5  # Fetch 5 pages per category (approx 100 items each)

    # Global Counter
    total_added = 0

    # --- 3. FETCH FUNCTION ---
    def fetch_and_save(endpoint, media_type, genre_name="Generic"):
        nonlocal total_added
        print(f"\nFetching {genre_name} ({media_type})...")
        
        current_batch_count = 0

        for page in range(1, PAGES_TO_FETCH + 1):
            # FIX: Handle ? vs & correctly
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
                        
                        if not poster or not backdrop or not title:
                            continue

                        try:
                            # Use INSERT OR IGNORE to skip duplicates
                            conn.execute("""
                                INSERT OR IGNORE INTO movies 
                                (tmdb_id, title, overview, poster_path, backdrop_path, release_date, vote_average, media_type, genre)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (tmdb_id, title, overview, poster, backdrop, date, rating, media_type, genre_name))
                            
                            total_added += 1
                            current_batch_count += 1
                            
                        except sqlite3.Error:
                            pass
                else:
                    print(f"  [!] Error on page {page}: {response.status_code}")
            
            except Exception as e:
                print(f"  [!] Crash: {e}")

            time.sleep(0.1) # Be nice to the API

        print(f"  -> Added {current_batch_count} items. (Total Database: {total_added})")

    # --- 4. EXECUTE ---
    fetch_and_save("movie/popular", "movie", "Popular")
    fetch_and_save("tv/popular", "tv", "TV Show")
    fetch_and_save("movie/top_rated", "movie", "Top Rated")

    for genre_id in genres:
        fetch_and_save(f"discover/movie?with_genres={genre_id}", "movie", f"Genre {genre_id}")

    conn.commit()
    conn.close()
    print(f"\nSUCCESS! Database seeding complete. Total Movies/Shows: {total_added}")

if __name__ == "__main__":
    save_to_db()