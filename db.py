import sqlite3
from typing import List, Tuple, Optional
import pandas as pd
from config import DB_PATH, MOVIES_CSV
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()

    # Movies table created for movie data
    cur.execute("""
    CREATE TABLE IF NOT EXISTS movies (
        movie_id INTEGER PRIMARY KEY,
        title TEXT NOT NULL
    )
    """)

    # Ratings table linking users to movies - requires
    # a unique constraint on user ID and movie ID.
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        movie_id INTEGER NOT NULL,
        rating REAL NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, movie_id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # Users table for authentication
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def import_movies_if_needed() -> None:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS c FROM movies")
    count = cur.fetchone()["c"]
    if count and count > 0:
        conn.close()
        return

    movies = pd.read_csv(MOVIES_CSV, usecols=["movieId", "title"])
    movies = movies.rename(columns={"movieId": "movie_id"})

    cur.executemany(
        "INSERT INTO movies(movie_id, title) VALUES (?, ?)",
        list(movies.itertuples(index=False, name=None))
    )
    conn.commit()
    conn.close()

def get_random_movies(limit: int = 30) -> List[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT movie_id, title FROM movies ORDER BY RANDOM() LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

def search_movies(query: str, limit: int = 30):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT movie_id, title
        FROM movies
        WHERE title LIKE ?
        ORDER BY title ASC
        LIMIT ?
    """, (f"%{query}%", limit))
    rows = cur.fetchall()
    conn.close()
    return rows


# Inserts or updates a rating using a unique costraint
# on user ID and movie ID
def upsert_rating(user_id: int, movie_id: int, rating: float) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO ratings(user_id, movie_id, rating)
    VALUES (?, ?, ?)
    ON CONFLICT(user_id, movie_id)
    DO UPDATE SET rating = excluded.rating, created_at = CURRENT_TIMESTAMP
    """, (user_id, movie_id, rating))
    conn.commit()
    conn.close()

# Deletes all rated movies from the user, allowing
# them to start over and create a new liked list.
def delete_all_user_ratings(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM ratings WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


# Retreieves all movies the user has rated.
def get_liked_movies(user_id: int, min_rating: float = 4.0):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.movie_id, m.title, r.rating
        FROM ratings r
        JOIN movies m ON r.movie_id = m.movie_id
        WHERE r.user_id = ? AND r.rating >= ?
        ORDER BY r.rating DESC, m.title ASC
    """, (user_id, min_rating))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_user_ratings(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT movie_id, rating FROM ratings WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [(int(r["movie_id"]), float(r["rating"])) for r in rows]


def get_titles_for_movie_ids(movie_ids: List[int]) -> List[Tuple[int, str]]:
    if not movie_ids:
        return []
    conn = get_conn()
    cur = conn.cursor()
    placeholders = ",".join(["?"] * len(movie_ids))
    query = f"SELECT movie_id, title FROM movies WHERE movie_id IN ({placeholders})"
    cur.execute(query, tuple(movie_ids))
    rows = cur.fetchall()
    conn.close()
    mapping = {int(r["movie_id"]): str(r["title"]) for r in rows}
    return [(mid, mapping.get(mid, "Unknown")) for mid in movie_ids]


# Creates the user based on their username and password.
def create_user(username: str, password_hash: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users(username, password_hash) VALUES (?, ?)",
        (username, password_hash)
    )
    conn.commit()
    conn.close()

# unfinished
def get_user_by_username(username: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return row

# unfinished
def get_user_by_id(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row
