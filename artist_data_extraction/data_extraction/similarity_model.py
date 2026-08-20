"""
Artist similarity from Essentia track features.

Pipeline:
  1. Load per-track Essentia features into a flat DataFrame (one row per track).
  2. Aggregate 5 tracks/artist -> one feature vector per artist (median, robust to
     an outlier track; std kept as extra features describing intra-artist spread).
  3. Standardize (z-score) all features.
  4. PCA (whitened) to auto-collapse redundant/correlated features -> a smaller,
     decorrelated feature space, keeping components that explain ~95% of variance.
  5. Compute both cosine similarity and Euclidean distance (on the whitened PCA
     space, so Euclidean here ~ Mahalanobis distance on the original features).
     Compare the two -- there's no universal "right" choice, validate against
     artists/genres you know.

Features are read straight out of a DuckDB `tracks` table with columns
(id, artist_id, raw_features_json), where raw_features_json is the raw
Essentia JSON blob for that track.
"""

import json

import duckdb
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances


# --------------------------------------------------------------------------
# 1. LOAD ESSENTIA FEATURES FROM DUCKDB INTO A FLAT DATAFRAME
# --------------------------------------------------------------------------
def flatten_dict(d, parent_key="", sep="."):
    """Flatten nested Essentia JSON (lowlevel/rhythm/tonal/...) into dot-keys.
    Numeric arrays (e.g. per-coefficient MFCC means) become one column per
    element, including nested lists (e.g. frame-level arrays), which are
    flattened recursively. Strings/bools (e.g. key name, scale) are dropped
    here -- if you want them, one-hot encode them separately rather than
    feeding raw strings into PCA/similarity.
    """
    items = {}

    def summarize_beats(beats_position):
        beats_position = np.array(beats_position)
        if len(beats_position) < 2:
            return {
                "rhythm.beats_count": len(beats_position),
                "rhythm.beat_interval_mean": np.nan,
                "rhythm.beat_interval_std": np.nan,
                "rhythm.tempo_estimate": np.nan,
            }
        intervals = np.diff(beats_position)
        return {
            "rhythm.beats_count": len(beats_position),
            "rhythm.beat_interval_mean": np.mean(intervals),   # avg time between beats
            "rhythm.beat_interval_std": np.std(intervals),      # rhythmic regularity/stability
            "rhythm.tempo_estimate": 60.0 / np.mean(intervals), # rough BPM from interval
        }

    def is_number(x):
        # bool is a subclass of int in Python, so explicitly exclude it
        return isinstance(x, (int, float)) and not isinstance(x, bool)

    def flatten_list(lst, key):
        for i, val in enumerate(lst):
            sub_key = f"{key}.{i}"
            if is_number(val):
                items[sub_key] = val
            elif isinstance(val, list):
                flatten_list(val, sub_key)  # recurse into nested lists
            elif isinstance(val, dict):
                items.update(flatten_dict(val, sub_key, sep=sep))  # rare, but handle it
            # else: string/bool/None inside a list -- silently dropped, same
            # policy as scalar strings/bools above
    VARIABLE_LENGTH_KEYS = {"rhythm.beats_position"}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if k in VARIABLE_LENGTH_KEYS and isinstance(v, list):
            items.update(summarize_beats(v))
        elif isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        elif isinstance(v, list):
            flatten_list(v, new_key)
        elif is_number(v):
            items[new_key] = v
        # else: string/bool/None scalar -- dropped, per original design

    return items

def flatten_dict_and_remove_list(d, parent_key="", sep="."):
    """Flatten nested Essentia JSON (lowlevel/rhythm/tonal/...) into dot-keys.
    Numeric arrays (e.g. per-coefficient MFCC means) become one column per
    element. Strings/bools (e.g. key name, scale) are dropped here -- if you
    want them, one-hot encode them separately rather than feeding raw strings
    into PCA/similarity.
    """
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        elif isinstance(v, list):
            continue
        elif isinstance(v, (int, float)):
            items[new_key] = v
    return items

def load_all_tracks(db_path):
    """
    Reads (id, artist_id, raw_features_json) from a DuckDB database and
    returns a flat DataFrame with one row per track: a 'track_id' column,
    an 'artist' column, plus one column per (flattened) Essentia feature.

    db_path: path to the .duckdb file.
    """
    con = duckdb.connect(db_path, read_only=True)
    try:
        return load_all_tracks_from_connection(con)
    finally:
        con.close()


def load_all_tracks_from_connection(con):
    """Same as load_all_tracks but takes an already-open duckdb connection,
    useful if your pipeline already has one open (e.g. in a notebook)."""
#     query_df = con.execute(f"""
#     SELECT t.id, a.name, t.artist_id, t.raw_features_json
#     FROM tracks t
#     JOIN artists a ON t.artist_id = a.id
#     WHERE t.artist_id IN (
#     SELECT artist_id
#     FROM tracks
#     GROUP BY artist_id
#     HAVING COUNT(*) = 5
#     LIMIT 100
# );
#     """).df()
    query_df = con.execute(f"""
    SELECT t.id, a.name, t.artist_id, t.raw_features_json
    FROM tracks t
    JOIN artists a ON t.artist_id = a.id;
    """).df()
    rows = []
    for _, r in query_df.iterrows():
        data = json.loads(r["raw_features_json"])
        flat = flatten_dict(data)
        flat["id"] = r["id"]
        flat["artist"] = r["name"]
        flat["artist_id"] = r["artist_id"]
        rows.append(flat)
    return pd.DataFrame(rows)


# df = load_all_tracks("features.duckdb")


# --------------------------------------------------------------------------
# 2. AGGREGATE TRACK FEATURES -> ARTIST FEATURES
# --------------------------------------------------------------------------
def build_artist_features(df):
    feature_cols = [c for c in df.columns if c not in ("track_id", "artist")]

    numeric = df[feature_cols].apply(pd.to_numeric, errors="coerce")
    numeric = numeric.dropna(axis=1, how="all")
    numeric = numeric.loc[:, numeric.nunique(dropna=True) > 1]  # drop constants
    numeric["artist"] = df["artist"]

    # Median across the 5 tracks: robust to one atypical song. Swap for .mean()
    # if you'd rather weight every track equally regardless of outliers.
    artist_median = numeric.groupby("artist").median()

    # Std across the 5 tracks per artist: captures "how consistent is this
    # artist's sound", a useful extra signal beyond the central tendency.
    artist_std = numeric.groupby("artist").std().add_suffix("_std")

    artist_features = artist_median.join(artist_std)
    artist_features = artist_features.fillna(artist_features.median())
    return artist_features


# --------------------------------------------------------------------------
# 3 & 4. STANDARDIZE + PCA (whitened)
# --------------------------------------------------------------------------
def reduce_features(artist_features, meta_cols, variance_target=0.95):
    feature_cols = [c for c in artist_features.columns if c not in meta_cols]
    X = artist_features[feature_cols].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    pca_full = PCA().fit(X_scaled)
    cum_var = np.cumsum(pca_full.explained_variance_ratio_)
    n_components = int(np.argmax(cum_var >= variance_target) + 1)
    print(
        f"Using {n_components} PCA components to explain "
        f"{variance_target:.0%} of variance "
        f"(reduced from {X_scaled.shape[1]} original dimensions)"
    )

    pca = PCA(n_components=n_components, whiten=True)
    X_pca = pca.fit_transform(X_scaled)

    meta = artist_features[meta_cols].reset_index(drop=True)
    return X_pca, pca, scaler, meta



# --------------------------------------------------------------------------
# 5. SIMILARITY
# --------------------------------------------------------------------------
def compute_similarity(artist_features, X_pca):
    artists = artist_features.index.tolist()
    cos_sim = cosine_similarity(X_pca)
    euclid_dist = euclidean_distances(X_pca)

    sim_df = pd.DataFrame(cos_sim, index=artists, columns=artists)
    dist_df = pd.DataFrame(euclid_dist, index=artists, columns=artists)
    return sim_df, dist_df


def most_similar(artist, sim_df, dist_df, k=10, method="cosine"):
    """method: 'cosine' (higher = more similar) or 'euclidean' (lower = more similar)"""
    if method == "cosine":
        return sim_df[artist].sort_values(ascending=False).iloc[1 : k + 1]
    else:
        return dist_df[artist].sort_values(ascending=True).iloc[1 : k + 1]

def convert_id_to_name(df, db_path):
    df = pd.DataFrame(df)
    ids = df.index.tolist()
    con = duckdb.connect(db_path, read_only=True)
    placeholders = ",".join(["?"] * len(ids))
    results = con.execute(f"SELECT name FROM artists where id in ({placeholders})", ids).fetchall()
    df["artist"] = [r[0] for r in results]
    # df["artist"] = [r[0] for r in results]
    con.close()
    return df

import duckdb
def get_names():
    import os
    DB_PATH = os.getenv("FEATURES_DB_PATH")
    con = duckdb.connect(DB_PATH)
    result = con.execute("select id, name from artists").fetchall()
    return result
lookup_table = dict(get_names())
def lookup_artist(id):
    return lookup_table[int(id)]
