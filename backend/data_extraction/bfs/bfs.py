from data_extraction.db_operations.save_features import *
from data_extraction.db_operations.get_features import *
from data_extraction.utils.wrapper import *
from loguru import logger
logger.add("data_extraction/bfs.log", level="INFO", rotation="10 MB")
logger.add("data_extraction/all.log", level="DEBUG", rotation="10 MB")
# seed_artist_list = [
#         "عمرو دياب",
#     "فيروز",
#     "ام كلثوم",
#     "محمد منير",
#     "نانسي عجرم",
#     "مرسيل خليفة",
#     "حسين الجسمي",
#     "Cairokee",
#     "Balti",
#     "Khaled",
# ]

# for artist in seed_artist_list:
#     add_artist_to_queue(artist, status="pending", depth=0)
try:

    while not is_queue_empty():
        artist_name, current_depth = get_artist_from_queue()
        update_artist_status(artist_name, status="processing")
        artist_object = call_and_save_lastfm_artist(artist_name)

        def do_if_not_failed(func, *args, **kwargs):
            status = get_artist_status(artist_name)
            if status == "failed":
                logger.info(f"Skipping {func.__name__} for artist {artist_name} ({artist_object['id']}) since status is failed")
                return None
            return func(*args, **kwargs)

        if artist_object.get('mbid', None) is not None:
            artist_object['name_en'] = do_if_not_failed(call_and_save_musicbrainz_artist, artist_object['mbid'], artist_name, artist_object['id'])
        else:
            artist_object['name_en'] = do_if_not_failed(search_musicbrainz_artist, artist_name, artist_object['id'])

        
        artist_object['itunes_artist_id'] = do_if_not_failed(call_and_save_itunes_artist, artist_object['name_en'], artist_object['id'], True)
        if artist_object['itunes_artist_id'] == "try_arabic":
            artist_object['itunes_artist_id'] = do_if_not_failed(call_and_save_itunes_artist, artist_object['name'], artist_object['id'], False)


        do_if_not_failed(call_and_save_track, artist_name, artist_object['itunes_artist_id'], artist_object['id'])

        similarity_list = call_and_save_similar_artists(artist_name, artist_object['id'])
        if similarity_list:
            for similar_artist in similarity_list:
                add_artist_to_queue(similar_artist[1], status="pending", depth=current_depth+1)

        do_if_not_failed(update_artist_status, artist_name, status="done")
except Exception as e:
    update_artist_status(artist_name, status="pending")
    raise e
