from loguru import logger
from data_extraction.db_operations.get_features import is_artist_queue_empty, get_artist_from_artist_queue
from data_extraction.utils.api_calls import call_musicbrainz_search
from data_extraction.utils.response_handling import handle_musicbrainz_search_response
from data_extraction.db_operations.save_features import insert_artist_from_musicbrainz, update_artist_status
from data_extraction.utils.wrapper import call_and_save_itunes_artist
from data_extraction.utils.utils import normalize_name
logger.add("process_existing/main.log", level="INFO", rotation="10 MB")

while not is_artist_queue_empty():
    artist_name, lastfm_listeners = get_artist_from_artist_queue()
    response = call_musicbrainz_search(artist_name)
    artist_object = None
    data = handle_musicbrainz_search_response(response, artist_name)
    if isinstance(data, dict):
        data['lastfm_listeners'] = lastfm_listeners
        data['name_key'] = normalize_name(data.get('name', artist_name))
        artist_object = insert_artist_from_musicbrainz(**data)
    else:
        logger.info(data[0])
        name_key = normalize_name(artist_name)
        artist_object = insert_artist_from_musicbrainz(None, "", [], "", artist_name, name_key, lastfm_listeners)
        
    if artist_object:
        if isinstance(data, dict):
            return_message = call_and_save_itunes_artist(artist_object['name_en'], artist_object['id'], True)
            if return_message == "try_arabic":
                return_message = call_and_save_itunes_artist(artist_name, artist_object['id'], False)
        else:
            call_and_save_itunes_artist(artist_name, artist_object['id'], True)

        update_artist_status(artist_name, status="done")
    else:
        update_artist_status(artist_name, status="failed")