import os
import duckdb
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH")
# 1. Connect to a local file.
# If 'arab_music_map.duckdb' doesn't exist, DuckDB creates it automatically.

con = duckdb.connect(DB_PATH)

print("Creating tables...")

# 2. Create the Artists table
# Stores general information about each artist.
con.execute("""
    CREATE TABLE IF NOT EXISTS artists (
        artist_id INTEGER PRIMARY KEY,
        artist_name VARCHAR NOT NULL UNIQUE,
        main_genre VARCHAR,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")

# 3. Create the Similarity Map table
# Uses DuckDB's native VARCHAR[] (List of Strings) to hold the 10 similar artists!
con.execute("""
    CREATE TABLE IF NOT EXISTS similarity_map (
        source_artist_name VARCHAR PRIMARY KEY,
        similar_artists VARCHAR[], -- Native array/list of strings
        cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")

logger.info("Database initialized successfully!")

# Always close the connection when done to flush writes to disk
con.close()