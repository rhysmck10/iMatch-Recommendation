from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from db import (
    init_db,
    import_movies_if_needed,
    get_random_movies,
    search_movies,
    upsert_rating,
    get_user_ratings,
    delete_all_user_ratings,
    get_titles_for_movie_ids,
    create_user,
    get_user_by_username,
    get_user_by_id,
    get_liked_movies
)
from recommender import build_artifacts, recommend
from tmdb_service import search_movie


# Initialises application, sets up database and builds 
# the recommendation model at startup.
def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = "dev-secret-change-me"

    # Import movies
    init_db()
    import_movies_if_needed()

    # Build recommender artifacts once.
    artifacts = build_artifacts(min_ratings_per_movie=5)
    def login_required(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in first.")
                return redirect(url_for("login"))
            return view_func(*args, **kwargs)
        return wrapped_view
    

    # Register route allows for user registration.
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if "user_id" in session:
            return redirect(url_for("index"))

        if request.method == "POST":
            username = request.form["username"].strip()
            password = request.form["password"].strip()

            if not username or not password:
                flash("Username and password are required.")
                return redirect(url_for("register"))

            existing = get_user_by_username(username)
            if existing:
                flash("Username already exists.")
                return redirect(url_for("register"))
            password_hash = generate_password_hash(password)
            create_user(username, password_hash)

            user = get_user_by_username(username)
            session["user_id"] = user["id"]
            flash("Registration successful.")
            return redirect(url_for("index"))
        return render_template("register.html")


    # Login route allows user to login with an existing username
    # and password.
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if "user_id" in session:
            return redirect(url_for("index"))

        if request.method == "POST":
            username = request.form["username"].strip()
            password = request.form["password"].strip()

            user = get_user_by_username(username)
            if not user or not check_password_hash(user["password_hash"], password):
                flash("Invalid username or password.")
                return redirect(url_for("login"))

            session["user_id"] = user["id"]
            flash("Logged in successfully.")
            return redirect(url_for("index"))
        return render_template("login.html")


    # Allows the user to log out of their account.
    @app.get("/logout")
    def logout():
        session.pop("user_id", None)
        flash("Logged out.")
        return redirect(url_for("login"))


    # Retrieves the list of movies and existing user ratings,
    # and passes them to the webpage.
    @app.get("/")
    @login_required
    def index():
        user_id = session["user_id"]
        q = request.args.get("q", "").strip()

        if q:
            movies = search_movies(q, limit=30)
        else:
            movies = get_random_movies(limit=30)

        user_ratings = dict(get_user_ratings(user_id))
        return render_template("index.html", movies=movies, user_ratings=user_ratings, q=q)


    # Processes user ratings, extracts the movie id and rating
    # from the form, validates the input and stores it using
    # the database function.
    @app.post("/rate")
    @login_required
    def rate():
        user_id = session["user_id"]

        movie_id = int(request.form["movie_id"])
        rating = float(request.form["rating"])
        q = request.form.get("q", "")

        if rating < 0 or rating > 5:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return {"success": False, "message": "Rating must be between 0 and 5."}, 400

            flash("Rating must be between 0 and 5.")
            return redirect(url_for("index", q=q))

        upsert_rating(user_id, movie_id, rating)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return {"success": True, "movie_id": movie_id, "rating": rating}

        return redirect(url_for("index", q=q))
    

    # Retrieves the users liked movies.
    @app.get("/liked")
    @login_required
    def liked_movies():
        user_id = session["user_id"]
        liked = get_liked_movies(user_id, min_rating=1.0)
        return render_template("liked.html", liked=liked)


    # Retrieves the user's ratings and passes them into
    # the recommendation function.
    @app.get("/recommendations")
    @login_required
    def recommendations():
        user_id = session["user_id"]
        user_ratings = get_user_ratings(user_id)

        recs = recommend(artifacts, user_ratings, top_n=10)
        rec_ids = [mid for mid, _ in recs]
        titles = get_titles_for_movie_ids(rec_ids)
        title_map = {mid: title for mid, title in titles}

        enriched = []
        for mid, score in recs:
            title = title_map.get(mid, "Unknown")
            tmdb = search_movie(title) or {}
            enriched.append({
                "movie_id": mid,
                "title": title,
                "score": round(score, 4),
                "poster_url": tmdb.get("poster_url"),
                "overview": tmdb.get("overview"),
                "release_date": tmdb.get("release_date"),
            })
        if not user_ratings:
            flash("Rate a few movies first so I can recommend something.")
        return render_template("recommendations.html", recs=enriched, has_ratings=bool(user_ratings))


    # Resets HTML.
    @app.get("/reset")
    @login_required
    def reset():
        return render_template("reset.html")


    # Resets all the users liked movies to 0.
    @app.post("/reset")
    @login_required
    def reset_post():
        user_id = session["user_id"]
        delete_all_user_ratings(user_id)
        flash("Your ratings have been cleared.")
        return redirect(url_for("index"))
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)