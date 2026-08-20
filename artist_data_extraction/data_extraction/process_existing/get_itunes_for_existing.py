from loguru import logger
from data_extraction.db_operations.get_features import get_artists_without_ids
from data_extraction.utils.api_calls import call_itunes_artist
from data_extraction.db_operations.save_features import save_artist_from_itunes
from data_extraction.utils.response_handling import handle_itunes_artist_response

artists = get_artists_without_ids()
for id, name in artists:
    logger.info(f"Searching Itunes for {name}")
    response = call_itunes_artist(name)
    data = handle_itunes_artist_response(response, name)
    if isinstance(data, dict):
        save_artist_from_itunes(data['itunes_artist_id'], id)
    else:
        if isinstance(data, tuple):
            logger.info(data[0])
        else:
            logger.info(data)

