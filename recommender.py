from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from config import RATINGS_CSV

@dataclass
class RecommenderArtifacts:
    movie_ids: np.ndarray              # columns in the matrix
    similarity_matrix: np.ndarray      # movie x movie cosine similarity
    movie_index: Dict[int, int]        # movieId -> column index


# Loads the MovieLens dataset and constructs a user-movie matrix.
# It then calculates similarity between movies based on user rating patterns.
def build_artifacts(min_ratings_per_movie: int = 20) -> RecommenderArtifacts:
    ratings = pd.read_csv(RATINGS_CSV, usecols=["userId", "movieId", "rating"])


    # Filter to movies with enough ratings (reduces noise + speeds up similarity)
    counts = ratings.groupby("movieId").size()
    keep_movies = counts[counts >= min_ratings_per_movie].index
    ratings = ratings[ratings["movieId"].isin(keep_movies)]


    # Create user-item matrix: rows users, cols movies
    pivot = ratings.pivot_table(index="userId", columns="movieId", values="rating").fillna(0.0)
    movie_ids = pivot.columns.to_numpy()
    matrix = pivot.to_numpy(dtype=np.float32)


    # Cosine similarity between columns (movies)
    # We want movie vectors: transpose so movies are rows
    movie_vectors = matrix.T
    sim = cosine_similarity(movie_vectors)
    movie_index = {int(mid): int(i) for i, mid in enumerate(movie_ids)}
    return RecommenderArtifacts(
        movie_ids=movie_ids.astype(int),
        similarity_matrix=sim.astype(np.float32),
        movie_index=movie_index
    )


# Takes the user's ratings and compares them to the similartiry matrix.
def recommend(artifacts, user_ratings, top_n: int = 10):
    if len(user_ratings) == 0:
        return []
    rated = [(mid, r) for mid, r in user_ratings if mid in artifacts.movie_index]
    if not rated:
        return []
    rated_ids = [mid for mid, _ in rated]
    rated_scores = np.array([r for _, r in rated], dtype=np.float32)


    # Convert ratings into preference weights.
    # Ratings are centered around a neutral value to distinguish
    # between positive and negative preferences.
    adjusted_scores = rated_scores - 3.0
    rated_indices = np.array(
        [artifacts.movie_index[mid] for mid in rated_ids],
        dtype=np.int32
    )
    sim_sub = artifacts.similarity_matrix[:, rated_indices]
    scores = sim_sub @ adjusted_scores
    rated_set = set(rated_ids)
    candidates = []
    for idx, mid in enumerate(artifacts.movie_ids):
        if int(mid) in rated_set:
            continue
        score = float(scores[idx])
        candidates.append((int(mid), score))
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[:top_n]