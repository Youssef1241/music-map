import time
import os
import pickle
from loguru import logger
from data_extraction.db_operations.get_features import retry_get_all_artists
from data_extraction.utils.wrapper import call_and_save_track
# logger.add("data_extraction/logs/preview_url_crawler.log", level="INFO", rotation="10 MB")
artists = retry_get_all_artists()
# print(artists)
# if os.path.exists("data_extraction/download_tracks/stopped_at.pkl"):
#     stopped_at = pickle.load(open("data_extraction/download_tracks/stopped_at.pkl", "rb"))
# else:
#     stopped_at = 0
for id, itunes_id, name in artists:
    try:
        call_and_save_track(name, itunes_id, id)
    except ConnectionError as e:
        logger.info(f"Error at artist {id}")
        time.sleep(10)
    except Exception as e:
        logger.info(f"Stopped at artist {id}")
        raise e