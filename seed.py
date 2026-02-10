import sqlite3
import requests
import time
from config import TMDB_API_KEY

# --- CONFIGURATION ---
NETFLIX_PROVIDER_ID = 8  
REGIONS = ["US", "IN"]   # Combine content from both regions
PAGES_TO_FETCH = 5       # 1 Page per region = ~40 items total per genre

def get_db_connection():
    conn = sqlite3.connect('netflix.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- HELPER: Get Logo ---
def get_logo(media_type, tmdb_id):
    """Fetches the best English PNG logo."""
    url = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}/images?api_key={TMDB_API_KEY}&include_image_language=en,null"
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            logos = data.get('logos', [])
            if logos:
                return logos[0]['file_path']
    except:
        pass
    return None

# --- HELPER: Get Real Age Rating ---
def get_real_certification(media_type, tmdb_id):
    """Fetches real age rating (PG-13, TV-MA, etc) from TMDB."""
    append_to = "release_dates" if media_type == "movie" else "content_ratings"
    url = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}?api_key={TMDB_API_KEY}&append_to_response={append_to}"
    
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            
            # 1. Handle Movies
            if media_type == "movie":
                releases = data.get("release_dates", {}).get("results", [])
                for country in releases:
                    if country["iso_3166_1"] in ["US", "IN"]:
                        # Return the first valid certification found
                        for release in country["release_dates"]:
                            if release["certification"]:
                                return release["certification"]
            
            # 2. Handle TV Shows
            else:
                ratings = data.get("content_ratings", {}).get("results", [])
                for rating in ratings:
                    if rating["iso_3166_1"] in ["US", "IN"]:
                        return rating["rating"]
                        
    except:
        pass
    
    # Fallback if API has no data
    return "PG-13" if media_type == "movie" else "TV-14"

def save_to_db():
    conn = get_db_connection()
    print("Starting Netflix-Only Database Update...")

    # 1. Create Tables (Added UNIQUE to tmdb_id to prevent duplicates)
    conn.execute("DROP TABLE IF EXISTS movies")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tmdb_id INTEGER UNIQUE,  /* Prevents US/IN duplicates */
            title TEXT,
            overview TEXT,
            poster_path TEXT,
            backdrop_path TEXT,
            logo_path TEXT,
            release_date TEXT,
            vote_average REAL,
            media_type TEXT,
            genre TEXT,
            age_rating TEXT
        )
    """)
    
    # User tables (Preserved)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT,
            avatar TEXT DEFAULT 'avatar-blue'
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

    # 3. Fetch Logic
    total_added = 0
    
    def fetch_and_save(base_params, media_type, genre_tag):
        nonlocal total_added
        print(f"\nFetching {genre_tag} ({media_type})...")
        
        # Loop through both regions (US and India)
        for region in REGIONS:
            print(f"  > Region: {region}", end=" ")
            
            for page in range(1, PAGES_TO_FETCH + 1):
                # Construct URL strictly for Netflix in that Region
                url = (f"https://api.themoviedb.org/3/discover/{media_type}?"
                       f"api_key={TMDB_API_KEY}&language=en-US&page={page}"
                       f"&watch_region={region}&with_watch_providers={NETFLIX_PROVIDER_ID}"
                       f"&{base_params}") # Append the specific sorting/genre logic
                
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

                            # Get Extra Details (Only if not already in DB to save time)
                            exists = conn.execute("SELECT 1 FROM movies WHERE tmdb_id = ?", (tmdb_id,)).fetchone()
                            if not exists:
                                logo = get_logo(media_type, tmdb_id)
                                age_rating = get_real_certification(media_type, tmdb_id)

                                try:
                                    conn.execute("""
                                        INSERT OR IGNORE INTO movies 
                                        (tmdb_id, title, overview, poster_path, backdrop_path, logo_path, release_date, vote_average, media_type, genre, age_rating)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (tmdb_id, title, overview, poster, backdrop, logo, date, rating, media_type, genre_tag, age_rating))
                                    
                                    total_added += 1
                                    print(".", end="", flush=True)
                                except sqlite3.Error:
                                    pass
                except Exception as e:
                    print(f"Error: {e}")
                
                time.sleep(0.2) # Respect API limits
            print("") # New line after region done

    # 4. Execute Mapped Queries
    # Note: We converted everything to 'discover' parameters to support the Netflix filter
    
    # "Trending" -> Popularity Descending
    fetch_and_save("sort_by=popularity.desc", "movie", "trending")
    
    # "Popular" -> Popularity Descending (Similar to trending, but keeps your tag)
    fetch_and_save("sort_by=popularity.desc&vote_count.gte=1000", "movie", "popular")
    
    # "New Releases" -> Release Date Descending
    fetch_and_save("sort_by=primary_release_date.desc&vote_count.gte=50", "movie", "new_releases")
    
    # "Action" -> Genre 28
    fetch_and_save("with_genres=28", "movie", "action")
    
    # "Anime" -> Genre 16 + Japanese
    fetch_and_save("with_genres=16&with_original_language=ja", "tv", "anime")
    
    # "US TV Drama" -> Genre 18 + English
    fetch_and_save("with_genres=18&with_original_language=en", "tv", "us_tv_drama")
    
    # "Bollywood" -> Hindi Language
    fetch_and_save("with_original_language=hi", "movie", "bollywood")
    
    # "K-Drama" -> Korean Language
    fetch_and_save("with_original_language=ko", "tv", "kdrama")
    
    # "Sci-Fi & Horror" -> Genres 878,27
    fetch_and_save("with_genres=878,27", "movie", "scifi_horror")

    conn.commit()
    conn.close()
    print(f"\nSUCCESS! Database seeded with {total_added} Netflix-verified titles.")

if __name__ == "__main__":
    save_to_db()