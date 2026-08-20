import os
import duckdb
from typing import List
from loguru import logger    
from typing import Literal
from dotenv import load_dotenv
from data_extraction.db_operations.get_features import get_row_count

load_dotenv()

DB_PATH = os.getenv("FEATURES_DB_PATH")

def save_artist_from_lastfm(mbid: str, name_key: str, name: str, lastfm_listeners: int) -> dict | None:
    con = duckdb.connect(DB_PATH)
    try:
        existing = con.execute(
            "SELECT * FROM artists WHERE mbid = ? OR name_key = ?",
            [mbid, name_key]
        ).fetchdf()

        if not existing.empty:
            logger.info(f"Artist {name_key} with MBID {mbid} already exists, skipping")
            return existing.iloc[0].to_dict()

        result = con.execute("""
            INSERT INTO artists (mbid, name_key, name, lastfm_listeners)
            VALUES (?, ?, ?, ?)
            RETURNING *
        """, (mbid, name_key, name, lastfm_listeners)).fetchdf()

        logger.info(f"Saved artist {name_key} with MBID {mbid}")
        return result.iloc[0].to_dict()

    except Exception as e:
        logger.error(f"Error saving artist {name_key} with MBID {mbid}: {e}")
        return None
    finally:
        con.close()

def save_artist_from_musicbrainz(mbid: str,country: str, artist_id: int, tags: List[str], name_en: str, name: str):
    con = duckdb.connect(DB_PATH)
    query = """
        UPDATE artists
        SET 
            mbid = CASE WHEN mbid IS NULL THEN ? ELSE mbid END,
            country = ?,
            tags = ?,
            name_en = ?,
            name = ?
        WHERE id = ?;
    """
    try:
        existing = con.execute("SELECT id FROM artists WHERE id = ?", [artist_id]).fetchone()
        if existing:
            result = con.execute(query, [mbid, country, tags, name_en, name, artist_id])
            logger.info(f"Updated artist with ID {artist_id}")
        else:
            logger.info(f"No artist found with this id {artist_id}, no action taken")
    except Exception as e:
        logger.error(f"Error saving artist with ID {artist_id}: {e}")
    finally:
        con.close()

def save_artist_from_itunes(itunes_artist_id: str, artist_id: str):
    con = duckdb.connect(DB_PATH)
    query = """
    UPDATE artists
    SET itunes_artist_id = ?
    WHERE id = ?;
    """
    try:
        existing = con.execute("SELECT id FROM artists WHERE id = ?", [artist_id]).fetchone()
        if existing:
            result = con.execute(query, (itunes_artist_id, artist_id))
            logger.info(f"Saved artist with id {artist_id} with iTunes ID {itunes_artist_id}")
        else:
            con.execute(
                """INSERT INTO artists (itunes_artist_id, id) VALUES (?, ?)""",
                (itunes_artist_id, artist_id)
            )
            logger.info(f"No artist found with this id {artist_id}, added new artist with iTunes ID {itunes_artist_id} and id {artist_id}")
    except Exception as e:
        logger.error(f"Error saving artist with id {artist_id} with iTunes ID {itunes_artist_id}: {e}")
    finally:
        con.close()

def save_track_from_itunes(itunes_track_id: str, artist_id: int, name: str, preview_url: str):
    con = duckdb.connect(DB_PATH)
    query = """
    INSERT INTO tracks (itunes_track_id, artist_id, name, preview_url) VALUES (?, ?, ?, ?);
    """
    try:

        existing = con.execute(
            "SELECT id FROM tracks WHERE itunes_track_id = ? AND artist_id = ?",
            [itunes_track_id, artist_id]
        ).fetchone()

        if existing:
            logger.info(f"Track {name} with iTunes ID {itunes_track_id} already exists, skipping")
            return

        con.execute(query, (itunes_track_id, artist_id, name, preview_url))
        logger.info(f"Added track with iTunes ID {itunes_track_id}")

    except Exception as e:
        logger.error(f"Error saving track with iTunes ID {itunes_track_id}: {e}")
    finally:
        con.close()


def save_track_features(features_list: list):
    con = duckdb.connect(DB_PATH)
    query = """
    UPDATE tracks
    SET raw_features_json = ?
    WHERE id = ?;
    """
    try:
        con.executemany(query, features_list)
        logger.info(f"Saved track features successfully")
    except Exception as e:
        logger.error(f"Error saving track features: {e}")
    finally:
        con.close()

def add_artist_to_queue(artist_name: str, status: str = Literal["pending", "processing", "done", "failed"], depth: int = 0):
    con = duckdb.connect(DB_PATH)
    query = """
    INSERT INTO crawl_queue (artist_name, status, depth) VALUES (?, ?, ?); 
    """
    try:
        existing = con.execute("SELECT artist_name FROM crawl_queue WHERE artist_name = ?", [artist_name]).fetchone()
        if existing:
            logger.debug(f"Artist {artist_name} already exists in crawl queue, skipping")
            return
        con.execute(query, (artist_name, status, depth, ))
        logger.debug(f"Added artist {artist_name} to crawl queue")
    except Exception as e:
        logger.error(f"Error updating crawl queue for artist {artist_name}: {e}")
    finally:
        con.close()

def update_artist_status(artist_name: str, status: str = Literal["pending", "processing", "done", "failed", "review"]):
    con = duckdb.connect(DB_PATH)
    query = """
    UPDATE artist_queue SET status = ? WHERE artist_name = ?;
    """
    try:
        existing = con.execute("SELECT artist_name FROM artist_queue WHERE artist_name = ?", [artist_name]).fetchone()
        if existing:
            con.execute(query, (status, artist_name))
            logger.info(f"Updated crawl queue for artist {artist_name}, status is now {status}")
        else:
            logger.info(f"No artist found with this name {artist_name}, no action taken")
    except Exception as e:
        logger.error(f"Error updating crawl queue for artist {artist_name}: {e}")
    finally:
        con.close()

def delete_artist_from_queue(artist_name):
    con = duckdb.connect(DB_PATH)
    query = """
    DELETE FROM crawl_queue WHERE artist_name = ?;
    """
    try:
        row_count = get_row_count("crawl_queue")
        con.execute(query, [artist_name])
        new_row_count = get_row_count("crawl_queue")
        if row_count == new_row_count:
            logger.info(f"No changes made deleting artist {artist_name} from crawl queue")
        else:
            logger.info(f"Deleted artist {artist_name} from crawl queue")
    except Exception as e:
        logger.error(f"Error deleting from crawl queue for artist {artist_name}: {e}")
    finally:
        con.close()

def update_failed_artist(artist_name: str, artist_id: int, problem: str, manual_review: bool = False):
    con = duckdb.connect(DB_PATH)
    query = """
    INSERT INTO failed_artists (artist_name, artist_id, problem, manual_review) VALUES (?, ?, ?, ?);
    """
    try:
        con.execute(query, (artist_name, artist_id, problem, manual_review))
    except Exception as e:
        logger.error(f"Error updating failed artist {artist_name}: {e}")
    finally:
        con.close()

def update_failed_track(problem: str, track_name: str = None, artist_id: id = None, track_id: int = None, manual_review: bool = False):
    con = duckdb.connect(DB_PATH)
    query = """
    INSERT INTO failed_tracks (track_name, artist_id, track_id, problem, manual_review) VALUES (?, ?, ?, ?, ?);
    """
    try:
        con.execute(query, (track_name, artist_id, track_id, problem, manual_review))
        logger.info(f"Updated failed track with artist id {artist_id} and track id {track_id}")
    except Exception as e:
        logger.error(f"Error updating failed track with artist id {artist_id} and track id {track_id}: {e}")
    finally:
        con.close()

def save_lastfm_similarities(artist_id: int, similar_artists: list[dict]):
    """
    similar_artists: list of dicts with keys 'similar_artist_name' and 'lastfm_score'
    """
    
    con = duckdb.connect(DB_PATH)
    try:
        con.executemany("""
            INSERT INTO artist_similarity_lastfm (artist_id, similar_artist_name, lastfm_score)
            VALUES (?, ?, ?)
            ON CONFLICT (artist_id, similar_artist_name) DO UPDATE SET
                lastfm_score = excluded.lastfm_score
        """, similar_artists)
        logger.info(f"Saved {len(similar_artists)} similarity scores for artist {artist_id}")
        return similar_artists
    except Exception as e:
        logger.error(f"Error saving similarities for artist {artist_id}: {e}")
    finally:
        con.close()
def insert_artist_from_musicbrainz(mbid: str, country: str, tags: List[str], name_en: str, name: str, name_key: str, lastfm_listeners: int):
    con = duckdb.connect(DB_PATH)
    query = """
        INSERT INTO artists (mbid, country, tags, name_en, name, name_key, lastfm_listeners)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        RETURNING *
    """
    try:
        result = con(query, (mbid, country, tags, name_en, name, name_key, lastfm_listeners)).fetchdf()

        logger.info(f"Saved artist {name_key} with MBID {mbid}")
        return result.iloc[0].to_dict()


    except Exception as e:
        logger.error(f"Error saving artist with MBID {mbid}: {e}")
        return None
    finally:
        con.close()

def update_lastfm_listeners(artist_id: int, lastfm_listeners: int):
    con = duckdb.connect(DB_PATH)
    query = """
        UPDATE artists SET lastfm_listeners = ? WHERE id = ?;
    """
    try:
        existing = con.execute("SELECT id FROM artists WHERE id = ?", [artist_id]).fetchone()
        if existing:
            result = con.execute(query, (lastfm_listeners, artist_id))
            logger.info(f"Updated artist with ID {artist_id}")
        else:
            logger.info(f"No artist found with this id {artist_id}, no action taken")
    except Exception as e:
        logger.error(f"Error saving artist with ID {artist_id}: {e}")
    finally:
        con.close()
