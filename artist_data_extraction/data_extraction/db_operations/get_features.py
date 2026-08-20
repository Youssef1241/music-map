from enum import unique
import os
from dotenv import load_dotenv
from loguru import logger    
import duckdb
from typing import Literal


load_dotenv()

DB_PATH = os.getenv("FEATURES_DB_PATH")
con = duckdb.connect(DB_PATH)

def get_row_count(table_name):
    count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    return count

def get_artist_from_queue():
    result = con.execute(
        "SELECT artist_name, depth FROM crawl_queue WHERE status = 'pending' LIMIT 1"
    ).fetchone()
    
    if result is None:
        return None, None  # queue is empty
    
    artist_name, depth = result  # unpack the tuple
    logger.info(f"Getting artist {artist_name} from queue at depth {depth}")
    return artist_name, depth

def get_all(table_name):
    
    try:
        result = con.execute(f"SELECT * FROM {table_name}").fetchall()
        logger.info(f"Retrieved {len(result)} from {table_name}")
        return result
    except Exception as e:
        logger.error(f"Error retrieving from {table_name}: {e}")
        return []

def get_artist_status(artist_name):
    result = con.execute(f"SELECT status FROM crawl_queue WHERE artist_name = ?", [artist_name]).fetchone()
    if result is None:
        return "failed"
    else:
        return result[0]

def is_queue_empty():
    result = con.execute(
        "SELECT artist_name, depth FROM crawl_queue WHERE status = 'pending'"
    ).fetchall()
    logger.info(f"There are {len(result)} pending artists remaining in the queue")
    return not bool(result)

def get_urls_from_id(artist_id):
    result = con.execute(
        "SELECT id, itunes_track_id, preview_url FROM tracks WHERE artist_id = ?",
        [artist_id]
    ).fetchall()
    return result

def get_urls():
    result = con.execute(
        "SELECT id, itunes_track_id, preview_url FROM tracks WHERE raw_features_json IS NULL").fetchall()
    return result

def get_all_ids():
    ids = con.execute("SELECT id FROM artists").df()['id'].tolist()
    return ids

def get_all_names():
    names = con.execute("SELECT artist_name FROM crawl_queue").df()['artist_name'].tolist()
    return names

def get_by_id(id):
    result = con.execute(f"SELECT mbid,name FROM artists WHERE id = ?", [id]).fetchone()
    if result is None:
        return None
    else:
        return result
def get_artist_from_artist_queue():
    result = con.execute(
        "SELECT artist_name, lastfm_listeners FROM artist_queue WHERE status = 'pending' LIMIT 1"
    ).fetchone()
    
    if result is None:
        return None, None  # queue is empty
    
    artist_name, lastfm_listeners = result  # unpack the tuple
    logger.info(f"Getting artist {artist_name} from queue at depth {lastfm_listeners}")
    return artist_name, lastfm_listeners

def is_artist_queue_empty():
    result = con.execute(
        "SELECT artist_name FROM artist_queue WHERE status = 'pending'"
    ).fetchall()
    logger.info(f"There are {len(result)} pending artists remaining in the queue")
    return not bool(result)

def get_artists_without_ids():
    result = con.execute("select id, name from artists where itunes_artist_id is null").fetchall()
    return result

def get_ids_and_names():
    result = con.execute("SELECT id, name FROM artists where lastfm_listeners = 0").fetchall()
    return result
def get_failed_artists():
    result = con.execute("""
    SELECT id, itunes_artist_id, name
    FROM artists
    WHERE id IN (
        SELECT DISTINCT artist_id
        FROM failed_tracks
    )
    """).fetchall()
    return result

def retry_get_all_artists():
    result = con.execute("""SELECT id, itunes_artist_id, name
        FROM artists
        WHERE id NOT IN (
            SELECT artist_id
            FROM tracks
            WHERE artist_id IS NOT NULL
        );""").fetchall()
    return result

def get_null_jsons():
    result = con.execute("""
    select id from artists where id in (select artist_id from tracks where raw_features_json is null)
    """).fetchall()
    return result

def get_listeners():
    result = con.execute("""
    select lastfm_listeners from artists
    """).fetchall()
    return result

def get_tracks_with_no_features():
    result = con.execute("""
    select id from tracks where raw_features_json is null
    """).fetchall()
    return result

def execute(query):
    result = con.execute(query).fetchall()
    return result

def getcon():
    return duckdb.connect(DB_PATH)