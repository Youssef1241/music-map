import os 
import duckdb
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

def save_to_similarity_cache(source_artist: str, similar_list: list):
    """
    Saves an artist and their top 10 similar artists into DuckDB.
    Overwrites the record if the source_artist already exists.
    """
    DB_PATH = os.getenv("DB_PATH")
    con = duckdb.connect(DB_PATH)
    
    # 2. Use 'INSERT OR REPLACE' so it acts as an upsert.
    # Note how we pass a native Python list directly into the execution tuple!
    query = """
        INSERT OR REPLACE INTO similarity_map (source_artist_name, similar_artists) 
        VALUES (?, ?);
    """
    
    con.execute(query, (source_artist, similar_list))
    
    # 3. Always close the connection to write changes safely to disk
    con.close()
    logger.info(f"Successfully cached {len(similar_list)} connections for '{source_artist}'.")


def get_similar_artists_from_cache(artist_name: str):
    """
    Checks the local database for an artist.
    Returns the list of similar artists if found, otherwise returns None.
    """
    DB_PATH = os.getenv("DB_PATH")
    con = duckdb.connect(DB_PATH)
    
    query = """
        SELECT similar_artists 
        FROM similarity_map 
        WHERE LOWER(source_artist_name) = LOWER(?);
    """
    
    # Fetch exactly one matching row
    result = con.execute(query, (artist_name,)).fetchone()
    con.close()
    
    if result:
        # result is a tuple, e.g., (['Hamaki', 'Tamer Hosny', ...],)
        # So we extract the 0-th element to get the clean Python list
        return result[0]
    
    return None

    