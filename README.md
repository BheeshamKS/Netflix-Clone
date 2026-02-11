# Netflix Clone

#### Video Demo: [Click Here](https://youtu.be/qkeoSfoD3f0)
## Description:
This project is a fully functional web-based streaming service clone inspired by Netflix. Built using Python, Flask, and SQLite, it mimics the core functionality of a major streaming platform, including user authentication, multiple profile management, dynamic content browsing, and a personalized "My List" feature.

The application leverages the TMDB (The Movie Database) API to fetch real-world movie and TV show data, including high-resolution posters, backdrops, and transparent logos. Unlike simple static websites, this project implements a complex backend architecture to simulate a production-level environment where users can maintain separate watch histories and preferences within a single household account.

### Key Features
#### Multi-Profile System: 
Just like the real Netflix, a single user account can have up to 5 distinct profiles. Each profile has its own unique "My List," ensuring that one user's saved shows do not clutter another's.

#### Dynamic Content Seeding: 
A custom Python script (seed.py) automates the population of the database. It fetches hundreds of titles across various genres (Anime, K-Drama, US TV, Action, etc.) and categorizes them for the frontend.

#### Responsive UI/UX: 
The frontend is built with custom CSS to be fully responsive. It mimics Netflix's behavior, such as the navigation bar transitioning from transparent to black on scroll, and the sophisticated "hover-to-expand" animations on movie cards.

#### Live Search with De-bouncing: 
The search bar allows users to find movies instantly. It uses JavaScript to send asynchronous requests to the backend, displaying results with official movie logos overlaid on backdrops.

#### JSON API Endpoints: 
The Flask backend serves not just HTML, but also JSON data. Endpoints like `/get_info/<id>` and `/search?q=...` allow the frontend to fetch media details without reloading the page, creating a Single Page Application (SPA) feel.

## Project Structure & File Description
The project is organized into a modular structure to separate concerns between the backend logic, database management, and frontend presentation.

### 1. Backend Logic (app.py)
This is the core entry point of the application. It initializes the Flask app, configures the SQLite database connection, and manages all routes.

#### Authentication: 
I used Flask-Login to handle user sessions. Routes like /login and /signup utilize werkzeug.security to hash passwords before storing them, ensuring security.

#### Profile Management: 
Routes such as /manage-profiles and /add-profile allow users to create, edit, and delete profiles. A custom context processor injects the active_profile into every template, so the UI always knows which avatar to display.

#### API Routes: 
To support the dynamic frontend, I created several JSON endpoints. For example, /add_to_list accepts a POST request to toggle a movie's saved status for the specific active profile.

### 2. Database Seeding (seed.py)
One of the most complex parts of this project was getting high-quality data. Instead of manually entering movies, I wrote this script to interact with the TMDB API.

It fetches content by specific genres (e.g., Genre ID 16 for Anime, 18 for Drama).

Standard API responses give posters, but not the specific English text logo (transparent PNG) that Netflix uses on its cards. This script makes an additional API call for every movie to fetch its logo_path and saves it to the local database.

It normalizes data from different regions (US and India) to ensure a diverse library.

### 3. Configuration (config.py & netflix.db)
`config.py`: Stores the API Key securely to keep it out of the main logic files.

`netflix.db`: A relational SQLite database. It features three main tables: users (accounts), profiles (linked to users via Foreign Key), and mylist (linked to profiles via Foreign Key). This schema design was critical for enabling the multi-profile feature.

### 4. Frontend Templates (templates/)
I used Jinja2 templating to render dynamic HTML.

`layout.htm`l: The master template containing the metadata, navigation bar, and footer. It uses Jinja blocks so child templates can inject their specific content.

`index.html`: The homepage. It renders multiple "Rows" of movies (Trending, New Releases, etc.) by iterating over database queries passed from Flask.

`my_list.htm`l: Displays the movies saved by the current profile. It includes logic to handle an "empty state" if the user hasn't saved anything yet.

`profiles.html` & `manage_profiles.html`: These pages manage the "Who's Watching?" experience, allowing users to switch contexts.

### 5. Static Assets (static/)
`styles.css`: Contains over 1,000 lines of custom CSS. I avoided frameworks like Bootstrap to have full control over the Netflix aesthetic. It handles the flexbox layouts for movie rows, the absolute positioning of text over images, and the media queries that adjust the grid for mobile devices (e.g., hiding text links on small screens).

`script.js`: Handles all client-side interactivity. Key functions include:

`openMoreInfo()`: Fetches movie details via AJAX and populates the modal window.

`toggleMyList()`: Sends a fetch request to add/remove items.

`handleSearch()`: A debounced function that waits for the user to stop typing before querying the server, reducing API load.

## Design Choices
Why SQLite instead of a JSON file? Initially, I considered storing movie data in a JSON file for simplicity. However, I realized that implementing a "My List" feature required relational data. A user has many profiles, and a profile has many saved movies. SQL was the only robust choice to handle these relationships and ensure data integrity (e.g., deleting a profile automatically cascades to delete its list).

Why separate the seed.py script? I debated fetching movie data in real-time every time a user loads the homepage. I decided against this for performance reasons. Making 20+ API calls to TMDB every time the index loads would be too slow and would quickly hit API rate limits. By creating a seeding script, the application serves data instantly from the local database, providing a much smoother user experience similar to a production app.

The "Logo" Logic: Standard movie apps just show a poster. To achieve the premium "Netflix" look, I needed the title to be an image (logo), not text. I designed the database schema to store a logo_path and wrote specific frontend logic: if a logo exists, show the image; if not, fallback to text. This small detail significantly elevated the visual quality of the project.

## Conclusion
This project was a deep dive into full-stack development. It required coordinating a Python backend with a complex database schema while maintaining a high standard of visual fidelity on the frontend. It demonstrates proficiency in API integration, database design, and responsive web development.