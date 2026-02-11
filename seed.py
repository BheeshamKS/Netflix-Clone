import sqlite3
import requests
import time
from config import TMDB_API_KEY

# --- CONFIGURATION ---
NETFLIX_PROVIDER_ID = 8  
REGIONS = ["US", "IN"]   
PAGES_TO_FETCH = 5        

def get_db_connection():
    conn = sqlite3.connect('netflix.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- HELPER: Get Logo ---
def get_logo(media_type, tmdb_id):
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
    append_to = "release_dates" if media_type == "movie" else "content_ratings"
    url = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}?api_key={TMDB_API_KEY}&append_to_response={append_to}"
    
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            
            if media_type == "movie":
                releases = data.get("release_dates", {}).get("results", [])
                for country in releases:
                    if country["iso_3166_1"] in ["US", "IN"]:
                        for release in country["release_dates"]:
                            if release["certification"]:
                                return release["certification"]
            else:
                ratings = data.get("content_ratings", {}).get("results", [])
                for rating in ratings:
                    if rating["iso_3166_1"] in ["US", "IN"]:
                        return rating["rating"]
    except:
        pass
    return "PG-13" if media_type == "movie" else "TV-14"

def save_to_db():
    conn = get_db_connection()
    print("Starting Netflix-Only Database Update...")

    conn.execute("DROP TABLE IF EXISTS movies")
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tmdb_id INTEGER UNIQUE,
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

    # Ensure other tables exist (just in case)
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
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            avatar TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mylist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER,
            tmdb_id INTEGER,
            media_type TEXT,
            FOREIGN KEY(profile_id) REFERENCES profiles(id)
        )
    """)

    # 3. Fetch Logic
    total_added = 0
    
    def fetch_and_save(base_params, media_type, genre_tag):
        nonlocal total_added
        print(f"\nFetching {genre_tag} ({media_type})...")
        
        clean_params = base_params.split('&page=')[0]

        for region in REGIONS:
            print(f"  > Region: {region}", end=" ")
            
            for page in range(1, PAGES_TO_FETCH + 1):
                url = (f"https://api.themoviedb.org/3/discover/{media_type}?"
                       f"api_key={TMDB_API_KEY}&language=en-US&page={page}"
                       f"&watch_region={region}&with_watch_providers={NETFLIX_PROVIDER_ID}"
                       f"&{clean_params}")
                
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

                            # Check if exists (Avoid re-fetching details)
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
                
                time.sleep(0.1) 
            print("") 

    # --- 4. EXECUTE MAPPED QUERIES ---
    
    # 1. TRENDING (Now includes Top TV Shows so big hits appear)
    fetch_and_save("sort_by=popularity.desc", "movie", "trending")
    fetch_and_save("sort_by=popularity.desc", "tv", "trending") # Added TV here!

    # 2. POPULAR (Movies)
    fetch_and_save("sort_by=popularity.desc&vote_count.gte=1000", "movie", "popular")

    # 3. NEW RELEASES
    fetch_and_save("sort_by=primary_release_date.desc&vote_count.gte=50", "movie", "new_releases")

    # 4. ACTION
    fetch_and_save("with_genres=28", "movie", "action")

    # 5. ANIME
    fetch_and_save("with_genres=16&with_original_language=ja", "tv", "anime")

    # 6. US TV DRAMA
    fetch_and_save("with_genres=18&with_original_language=en", "tv", "us_tv_drama")

    # 7. BOLLYWOOD
    fetch_and_save("with_original_language=hi", "movie", "bollywood")

    # 8. K-DRAMA
    fetch_and_save("with_original_language=ko", "tv", "kdrama")

    # 9. SCI-FI & HORROR 
    # Fetch Movies (Sci-Fi + Horror)
    fetch_and_save("with_genres=878,27", "movie", "scifi_horror")
    # Fetch TV (Sci-Fi & Fantasy)
    fetch_and_save("with_genres=10765", "tv", "scifi_horror") 

    conn.commit()
    conn.close()
    print(f"\nSUCCESS! Database seeded with {total_added} Netflix-verified titles.")

if __name__ == "__main__":
    save_to_db()