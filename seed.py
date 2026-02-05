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

    # MAPPING: The Label you want -> The TMDB Query parameters
    categories = {
        "popular":       ("movie/popular", {}),
        "trending":      ("trending/movie/week", {}),
        "new_releases":  ("movie/upcoming", {}),
        "action":        ("discover/movie", {"with_genres": "28"}),
        "anime":         ("discover/tv", {"with_genres": "16", "with_keywords": "210024"}), # 16=Animation
        "us_tv_drama":   ("discover/tv", {"with_genres": "18", "with_original_language": "en", "region": "US"}),
        "bollywood":     ("discover/movie", {"with_original_language": "hi", "region": "IN"}),
        "scifi_horror":  ("discover/tv", {"with_genres": "10765"}), # Sci-Fi & Fantasy
        "kdrama":        ("discover/tv", {"with_original_language": "ko", "with_genres": "18"}),
    }

    print("Clearing old data...")
    db.execute("DELETE FROM movies") # Start fresh so we don't have duplicates

    for genre_tag, (endpoint, params) in categories.items():
        print(f"Fetching {genre_tag}...")
        movies = get_movies(endpoint, params)
        
        for movie in movies:
            try:
                # TMDB uses 'name' for TV shows and 'title' for Movies. We handle both.
                title = movie.get('title', movie.get('name'))
                if not title: continue

                poster = f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}"
                backdrop = f"https://image.tmdb.org/t/p/original{movie.get('backdrop_path')}"
                
                db.execute("""
                    INSERT INTO movies 
                    (tmdb_id, title, overview, poster_path, backdrop_path, release_date, vote_average, genre)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    movie['id'],
                    title,
                    movie.get('overview', ''),
                    poster,
                    backdrop,
                    movie.get('release_date', movie.get('first_air_date')),
                    movie['vote_average'],
                    genre_tag 
                ))
            except Exception as e:
                pass # Skip duplicates

    conn.commit()
    conn.close()
    print("Success! Database populated with all categories.")

if __name__ == "__main__":
    save_to_db()