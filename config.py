import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
MOVIES_CSV = os.path.join(DATA_DIR, "movies.csv")
RATINGS_CSV = os.path.join(DATA_DIR, "ratings.csv")

DB_PATH = os.path.join(BASE_DIR, "imatch.sqlite3")

# Optional TMDb
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")  # set in env if you want posters
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"