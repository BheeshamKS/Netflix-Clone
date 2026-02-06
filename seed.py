import requests
import sqlite3

# --- CONFIGURATION ---
API_KEY = "2a11b3a974a0295138449ec38fffdf26"  # <--- MAKE SURE YOUR KEY IS HERE
DB_NAME = "netflix.db"
# ---------------------

def get_movies(endpoint, params=None):
    if params is None:
        params = {}
    url = f"https://api.themoviedb.org/3/{endpoint}?api_key={API_KEY}&language=en-US&page=1"
    for key, value in params.items():
        url += f"&{key}={value}"
        
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()["results"]
    else:
        print(f"Error fetching: {response.status_code}")
        return []

def save_to_db():
    conn = sqlite3.connect(DB_NAME)
    db = conn.cursor()

    # 1. DROP and RE-CREATE Table with the new 'media_type' column
    print("Resetting database schema...")
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
            media_type TEXT  -- <--- NEW COLUMN ('movie' or 'tv')
        )
    """)

    # 2. DEFINE CATEGORIES + THEIR TYPE
    # Format: "tag": ("endpoint", {params}, "movie" OR "tv")
    categories = {
        # --- MOVIES ---
        "popular":       ("movie/popular", {}, "movie"),
        "trending":      ("trending/movie/week", {}, "movie"),
        "new_releases":  ("movie/upcoming", {}, "movie"),
        "action":        ("discover/movie", {"with_genres": "28"}, "movie"),
        "bollywood":     ("discover/movie", {"with_original_language": "hi", "region": "IN"}, "movie"),
        
        # --- TV SHOWS ---
        "anime":         ("discover/tv", {"with_genres": "16", "with_keywords": "210024"}, "tv"),
        "us_tv_drama":   ("discover/tv", {"with_genres": "18", "with_original_language": "en", "region": "US"}, "tv"),
        "scifi_horror":  ("discover/tv", {"with_genres": "10765"}, "tv"),
        "kdrama":        ("discover/tv", {"with_original_language": "ko", "with_genres": "18"}, "tv"),
    }

    # 3. FETCH AND SAVE
    for genre_tag, (endpoint, params, m_type) in categories.items():
        print(f"Fetching {genre_tag} ({m_type})...")
        items = get_movies(endpoint, params)
        
        for item in items:
            try:
                # TV shows use 'name', Movies use 'title'. We grab whichever exists.
                title = item.get('title', item.get('name'))
                date = item.get('release_date', item.get('first_air_date'))
                
                if not title: continue

                poster = f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}"
                backdrop = f"https://image.tmdb.org/t/p/original{item.get('backdrop_path')}"
                
                db.execute("""
                    INSERT INTO movies 
                    (tmdb_id, title, overview, poster_path, backdrop_path, release_date, vote_average, genre, media_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item['id'],
                    title,
                    item.get('overview', ''),
                    poster,
                    backdrop,
                    date,
                    item['vote_average'],
                    genre_tag,
                    m_type # <--- Saving 'movie' or 'tv'
                ))
            except Exception as e:
                pass 

    conn.commit()
    conn.close()
    print("Success! Database updated with separate Movie/TV types.")

if __name__ == "__main__":
    save_to_db()