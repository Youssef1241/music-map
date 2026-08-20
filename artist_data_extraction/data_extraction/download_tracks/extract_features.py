from data_extraction.utils.wrapper import call_and_save_track_features
from data_extraction.db_operations.get_features import get_null_jsons
from pushbullet import Pushbullet
import pickle
import os
from loguru import logger
from dotenv import load_dotenv
load_dotenv()
logger.add("data_extraction/logs/extract_features.log", level="INFO", rotation="10 MB")
artists = get_null_jsons()
if os.path.exists("data_extraction/download_tracks/stopped_at.pkl"):
    stopped_at = pickle.load(open("data_extraction/download_tracks/stopped_at.pkl", "rb"))
else:
    stopped_at = 0
artists = artists[stopped_at:] if stopped_at > 0 else artists
for i, artist_id in enumerate(artists):
    try:
        logger.info(f"Calling and saving track features for artist {artist_id}, id {i}")
        call_and_save_track_features(artist_id)
    except Exception as e:
        logger.info(f"Stopped at ID: {i}")
        with open("data_extraction/download_tracks/stopped_at.pkl", "wb") as f:
            pickle.dump(artists.index(artist_id), f)
        raise e
    except KeyboardInterrupt:
        logger.info(f"Stopped at ID: {i}")
        with open("data_extraction/download_tracks/stopped_at.pkl", "wb") as f:
            pickle.dump(artists.index(artist_id), f)

