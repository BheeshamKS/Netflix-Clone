from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
import sqlite3
import random
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from config import TMDB_API_KEY

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # Needed for sessions

# --- LOGIN SETUP ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Redirect here if not logged in

# User Class for Flask-Login
class User(UserMixin):
    def __init__(self, id, email, name):
        self.id = id
        self.email = email
        self.name = name

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        return User(id=user['id'], email=user['email'], name=user['name'])
    return None

# Helper function to connect to the database
def get_db_connection():
    conn = sqlite3.connect('netflix.db')
    conn.row_factory = sqlite3.Row  # Crucial: allows us to use movie['title']
    return conn

# --- AUTH ROUTES ---

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form.get('name', 'User')

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

        if user:
            flash('Email already exists')
            conn.close()
            return redirect(url_for('signup'))

        # Create new user
        hashed_pw = generate_password_hash(password, method='scrypt')
        
        # 1. Get the cursor so we can grab the new ID
        cursor = conn.execute('INSERT INTO users (email, password, name) VALUES (?, ?, ?)', 
                     (email, hashed_pw, name))
        new_user_id = cursor.lastrowid

        # --- RANDOM COLOR ASSIGNMENT ---
        colors = ['blue', 'red', 'green', 'yellow', 'purple']
        avatar_color = random.choice(colors)

        conn.execute('INSERT INTO profiles (user_id, name, avatar) VALUES (?, ?, ?)',
                     (new_user_id, name, avatar_color)) # Saving 'blue', 'red', etc.
        
        conn.commit()
        conn.close()
        
        # 3. Auto Login
        new_user = User(id=new_user_id, email=email, name=name)
        login_user(new_user)
        
        # 4. Send to Profile Selection
        return redirect(url_for('browse_profiles'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()

        # CASE 1: Email does not exist
        if not user:
            flash("Account not found. This is a free clone! Please Sign Up first.")
            return redirect(url_for('login'))
        
        # CASE 2: Wrong Password
        if not check_password_hash(user['password'], password):
            flash("Incorrect password. Please try again.")
            return redirect(url_for('login'))

        # CASE 3: Success
        user_obj = User(id=user['id'], email=user['email'], name=user['name'])
        login_user(user_obj)
        
        # CHANGE: Redirect to "Who's Watching?" instead of Home
        return redirect(url_for('browse_profiles'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    # Clear session data
    session.pop('profile_id', None)
    session.pop('profile_name', None)
    return redirect(url_for('index'))


# --- PROFILE ROUTES (NEW) ---

@app.route('/profiles')
@login_required
def browse_profiles():
    conn = get_db_connection()
    # Fetch all profiles belonging to this user
    profiles = conn.execute('SELECT * FROM profiles WHERE user_id = ?', (current_user.id,)).fetchall()
    conn.close()
    return render_template('profiles.html', profiles=profiles)

@app.route('/set_profile/<int:profile_id>')
@login_required
def set_profile(profile_id):
    # Security: Ensure this profile actually belongs to the logged-in user!
    conn = get_db_connection()
    profile = conn.execute('SELECT * FROM profiles WHERE id = ? AND user_id = ?', 
                           (profile_id, current_user.id)).fetchone()
    conn.close()
    
    if profile:
        # Save Profile to Session
        session['profile_id'] = profile['id']
        session['profile_name'] = profile['name']
        session['profile_avatar'] = profile['avatar']
        return redirect(url_for('index'))
    else:
        flash("Invalid Profile")
        return redirect(url_for('browse_profiles'))

@app.route('/add-profile', methods=['GET', 'POST'])
@login_required
def add_profile():
    if request.method == 'POST':
        name = request.form['name']
        
        if name:
            conn = get_db_connection()
            # 1. Limit profiles to 5 (Netflix style)
            # We fetch one row and get the first column (the count)
            count = conn.execute('SELECT COUNT(*) FROM profiles WHERE user_id = ?', (current_user.id,)).fetchone()[0]
            
            if count < 5:
                # --- RANDOM COLOR ASSIGNMENT ---
                colors = ['blue', 'red', 'green', 'yellow', 'purple']
                avatar_color = random.choice(colors)

                conn.execute('INSERT INTO profiles (user_id, name, avatar) VALUES (?, ?, ?)',
                             (current_user.id, name, avatar_color))
                conn.commit()
            else:
                flash("Maximum 5 profiles allowed.")
            
            conn.close()
            return redirect(url_for('browse_profiles'))

    return render_template('add_profile.html')

# --- MANAGE PROFILES ROUTES ---

@app.route('/manage-profiles')
@login_required
def manage_profiles():
    conn = get_db_connection()
    profiles = conn.execute('SELECT * FROM profiles WHERE user_id = ?', (current_user.id,)).fetchall()
    conn.close()
    return render_template('manage_profiles.html', profiles=profiles)

@app.route('/edit-profile/<int:profile_id>', methods=['GET', 'POST'])
@login_required
def edit_profile(profile_id):
    conn = get_db_connection()
    
    # 1. Security Check: Verify profile belongs to current user
    profile = conn.execute('SELECT * FROM profiles WHERE id = ? AND user_id = ?', 
                           (profile_id, current_user.id)).fetchone()
    
    if not profile:
        conn.close()
        return redirect(url_for('manage_profiles'))

    # 2. Handle Update
    if request.method == 'POST':
        new_name = request.form['name']
        
        conn.execute('UPDATE profiles SET name = ? WHERE id = ?', (new_name, profile_id))
        conn.commit()
        conn.close()
        
        # Update session if we just edited the active profile
        if session.get('profile_id') == profile_id:
            session['profile_name'] = new_name
            
        return redirect(url_for('manage_profiles'))

    conn.close()
    return render_template('edit_profile.html', profile=profile)

@app.route('/delete-profile/<int:profile_id>')
@login_required
def delete_profile(profile_id):
    conn = get_db_connection()
    
    # 1. Prevent deleting the last profile
    count = conn.execute('SELECT COUNT(*) FROM profiles WHERE user_id = ?', (current_user.id,)).fetchone()[0]
    
    if count <= 1:
        flash("You cannot delete your only profile.")
        conn.close()
        return redirect(url_for('manage_profiles'))

    # 2. Delete
    conn.execute('DELETE FROM profiles WHERE id = ? AND user_id = ?', (profile_id, current_user.id))
    conn.commit()
    conn.close()
    
    # 3. Handle Session (If we deleted the active profile, log them out of the profile)
    if session.get('profile_id') == profile_id:
        session.pop('profile_id', None)
        session.pop('profile_name', None)
        session.pop('profile_avatar', None)
        
    return redirect(url_for('manage_profiles'))


@app.context_processor
def inject_user_data():
    """
    Injects 'all_profiles' AND 'active_profile' into every page.
    """
    data = {}
    if current_user.is_authenticated:
        conn = get_db_connection()
        
        # 1. Get ALL profiles (for the dropdown list)
        profiles = conn.execute('SELECT * FROM profiles WHERE user_id = ?', (current_user.id,)).fetchall()
        data['all_profiles'] = profiles
        
        # 2. Get ACTIVE profile (to color the top-right avatar)
        active_profile_id = session.get('profile_id')
        
        if active_profile_id:
            # Find the profile that matches the session ID
            active_profile = conn.execute('SELECT * FROM profiles WHERE id = ?', (active_profile_id,)).fetchone()
            data['active_profile'] = active_profile
        else:
            # Fallback: If no profile selected yet, use the first one
            if profiles:
                data['active_profile'] = profiles[0]
            else:
                data['active_profile'] = None

        conn.close()
    return data


# --- MY LIST API ---

@app.route('/add_to_list/<media_type>/<int:tmdb_id>', methods=['POST'])
@login_required
def add_to_list(media_type, tmdb_id):
    # Ensure a profile is selected
    if 'profile_id' not in session:
        return jsonify({'error': 'No profile selected'}), 403

    conn = get_db_connection()
    media_type = media_type.lower()
    
    # Check if it exists (using USER_ID for now, later we can switch to PROFILE_ID if you want per-profile lists)
    exists = conn.execute('SELECT * FROM mylist WHERE user_id = ? AND tmdb_id = ? AND media_type = ?', 
                          (current_user.id, tmdb_id, media_type)).fetchone()
    
    if exists:
        conn.execute('DELETE FROM mylist WHERE user_id = ? AND tmdb_id = ? AND media_type = ?',
                     (current_user.id, tmdb_id, media_type))
        status = 'removed'
    else:
        local_movie = conn.execute('SELECT * FROM movies WHERE tmdb_id = ? AND media_type = ?', 
                                   (tmdb_id, media_type)).fetchone()
        
        if not local_movie:
            url = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}?api_key={TMDB_API_KEY}&language=en-US"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                title = data.get('title') or data.get('name')
                poster = data.get('poster_path')
                backdrop = data.get('backdrop_path')
                date = data.get('release_date') or data.get('first_air_date')
                overview = data.get('overview')
                rating = data.get('vote_average')
                
                conn.execute("""
                    INSERT INTO movies (tmdb_id, title, overview, poster_path, backdrop_path, 
                                      release_date, vote_average, media_type, genre)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'user_saved')
                """, (tmdb_id, title, overview, poster, backdrop, date, rating, media_type))
        
        conn.execute('INSERT INTO mylist (user_id, tmdb_id, media_type) VALUES (?, ?, ?)',
                     (current_user.id, tmdb_id, media_type))
        status = 'added'
        
    conn.commit()
    conn.close()
    return jsonify({'status': status})


@app.route('/my-list')
@login_required
def my_list():
    conn = get_db_connection()
    saved_items = conn.execute("""
        SELECT movies.* FROM mylist 
        JOIN movies ON mylist.tmdb_id = movies.tmdb_id AND mylist.media_type = movies.media_type
        WHERE mylist.user_id = ?
        GROUP BY movies.tmdb_id
    """, (current_user.id,)).fetchall()
    
    conn.close()
    return render_template('my_list.html', saved_items=saved_items)

@app.route('/')
def index():
    # Force Login if not authenticated
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
        
    # Force Profile Selection if logged in but no profile set
    if 'profile_id' not in session:
        return redirect(url_for('browse_profiles'))

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
    
    popular = conn.execute("SELECT * FROM movies WHERE genre='popular'").fetchall()
    trending = conn.execute("SELECT * FROM movies WHERE genre='trending'").fetchall()
    new_releases = conn.execute("SELECT * FROM movies WHERE genre='new_releases'").fetchall()
    anime = conn.execute("SELECT * FROM movies WHERE genre='anime'").fetchall()
    us_tv = conn.execute("SELECT * FROM movies WHERE genre='us_tv_drama'").fetchall()
    bollywood = conn.execute("SELECT * FROM movies WHERE genre='bollywood'").fetchall()
    scifi = conn.execute("SELECT * FROM movies WHERE genre='scifi_horror'").fetchall()
    kdrama = conn.execute("SELECT * FROM movies WHERE genre='kdrama'").fetchall()
    action = conn.execute("SELECT * FROM movies WHERE genre='action'").fetchall()

    if popular:
        featured = random.choice(popular)
    else:
        featured = None

    conn.close()
    
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

@app.route('/tvshows')
@login_required
def tv_shows():
    if 'profile_id' not in session: return redirect(url_for('browse_profiles'))
    
    conn = get_db_connection()

    us_tv = conn.execute("SELECT * FROM movies WHERE genre='us_tv_drama'").fetchall()
    kdrama = conn.execute("SELECT * FROM movies WHERE genre='kdrama'").fetchall()
    anime = conn.execute("SELECT * FROM movies WHERE genre='anime'").fetchall()
    scifi = conn.execute("SELECT * FROM movies WHERE genre='scifi_horror'").fetchall()
    
    if us_tv:
        featured = random.choice(us_tv)
    elif kdrama:
        featured = random.choice(kdrama)
    else:
        featured = None

    conn.close()

    return render_template('tv_shows.html', 
                           featured_movie=featured,
                           us_tv_shows=us_tv,
                           kdramas=kdrama,
                           anime_shows=anime,
                           scifi_shows=scifi)

@app.route('/movies')
@login_required
def movies():
    if 'profile_id' not in session: return redirect(url_for('browse_profiles'))

    conn = get_db_connection()

    popular = conn.execute("SELECT * FROM movies WHERE genre='popular'").fetchall()
    action = conn.execute("SELECT * FROM movies WHERE genre='action'").fetchall()
    bollywood = conn.execute("SELECT * FROM movies WHERE genre='bollywood'").fetchall()
    new_releases = conn.execute("SELECT * FROM movies WHERE genre='new_releases'").fetchall()
    trending = conn.execute("SELECT * FROM movies WHERE genre='trending'").fetchall()

    if trending:
        featured = random.choice(trending)
    elif popular:
        featured = random.choice(popular)
    else:
        featured = None

    conn.close()

    return render_template('movies.html', 
                           featured_movie=featured,
                           popular_movies=popular,
                           action_movies=action,
                           bollywood_movies=bollywood,
                           new_releases=new_releases,
                           trending_movies=trending)

@app.route('/get_trailer/<media_type>/<int:tmdb_id>')
def get_trailer(media_type, tmdb_id):
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

    results = fetch_videos_from_tmdb(media_type, tmdb_id)

    if not results:
        fallback_type = 'tv' if media_type == 'movie' else 'movie'
        results = fetch_videos_from_tmdb(fallback_type, tmdb_id)

    if results:
        for video in results:
            if video['site'] == 'YouTube' and video['type'] == 'Trailer':
                return jsonify({'key': video['key']})
        
        if results[0]['site'] == 'YouTube':
             return jsonify({'key': results[0]['key']})

    return jsonify({'error': 'No trailer found'}), 404

@app.route('/new-popular')
@login_required
def new_popular():
    if 'profile_id' not in session: return redirect(url_for('browse_profiles'))
    
    conn = get_db_connection()

    new_releases = conn.execute("SELECT * FROM movies WHERE genre='new_releases'").fetchall()
    trending_movies = conn.execute("SELECT * FROM movies WHERE genre='trending'").fetchall()
    top_tv = conn.execute("SELECT * FROM movies WHERE genre='us_tv_drama'").fetchall()
    coming_soon = conn.execute("SELECT * FROM movies WHERE genre='popular'").fetchall()
    worth_wait = conn.execute("SELECT * FROM movies WHERE genre='action'").fetchall()

    conn.close()

    return render_template('new_popular.html', 
                           new_releases=new_releases,
                           trending_movies=trending_movies,
                           top_tv_shows=top_tv,
                           coming_soon=coming_soon,
                           worth_wait=worth_wait)

@app.route('/get_info/<media_type>/<int:tmdb_id>')
def get_info(media_type, tmdb_id):
    url = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}?api_key={TMDB_API_KEY}&language=en-US&append_to_response=credits,images&include_image_language=en,null"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify({'error': 'Not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    conn = get_db_connection()
    # Fetch results
    results = conn.execute("""
        SELECT * FROM movies 
        WHERE title LIKE ? 
        ORDER BY vote_average DESC 
        LIMIT 20
    """, ('%' + query + '%',)).fetchall()
    conn.close()

    movies_list = []
    for movie in results:
        movies_list.append({
            'id': movie['tmdb_id'],
            'title': movie['title'],
            'media_type': movie['media_type'],
            'backdrop_path': movie['backdrop_path'],
            'logo_path': movie['logo_path'],    # <--- THIS LINE IS REQUIRED
            'age_rating': movie['age_rating']
        })

    return jsonify(movies_list)


if __name__ == '__main__':
    app.run(debug=True)