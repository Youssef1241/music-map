import traceback
from data_extraction.utils.api_calls import *
from data_extraction.db_operations.save_features import *
from data_extraction.utils.response_handling import *

def call_and_save_lastfm_artist(artist_name: str):
    response = call_lastfm(artist_name, False)
    data = handle_lastfm_getInfo_response(response)
    if isinstance(data, dict):
        artist_id = save_artist_from_lastfm(**data)
        return artist_id
    else:
        update_failed_artist(artist_name, None, data)
        update_artist_status(artist_name, status="failed")
def call_and_save_similar_artists(artist_name: str, artist_id: int):
    response = call_lastfm(artist_name, True)
    data = handle_lastfm_getSimilar_response(response, artist_id)
    if isinstance(data, list):
        similarity_list = save_lastfm_similarities(artist_id=artist_id, similar_artists=data)
        return similarity_list
    else:
        update_failed_artist(artist_name, artist_id, data)
        update_artist_status(artist_name, status="failed")

def search_musicbrainz_artist(artist_name: str, artist_id: int):
    response = call_musicbrainz_search(artist_name)
    data = handle_musicbrainz_search_response(response, artist_name)
    if isinstance(data, dict):
        data['artist_id'] = artist_id
        save_artist_from_musicbrainz(**data)
        return data['name_en']
    else:
        if isinstance(data, tuple):
            update_failed_artist(artist_name, artist_id, data[0], data[1])
        else:
            update_failed_artist(artist_name, artist_id, data)  
        update_artist_status(artist_name, status="failed")

def call_and_save_musicbrainz_artist(mbid: str, artist_name: str, artist_id: int):
    response = call_musicbrainz(mbid)
    data = handle_musicbrainz_response(response, artist_name)
    if isinstance(data, dict):
        data['artist_id'] = artist_id
        save_artist_from_musicbrainz(**data)
        return data['name_en']
    else:
        if isinstance(data, tuple):
            update_failed_artist(artist_name, artist_id, data[0], data[1])
        else:
            update_failed_artist(artist_name, artist_id, data)
        update_artist_status(artist_name, status="failed")

def call_and_save_itunes_artist(artist_name: str, artist_id: int, first_time: bool):
    if not first_time:
        contains_arabic = bool(re.search(r'[\u0600-\u06FF]', artist_name))
        if not contains_arabic:
            update_failed_artist(artist_name, artist_id, f"No itunes matches found for {artist_name}, saving to failed_artists", True)
            update_artist_status(artist_name, status="failed")
            return None
    response = call_itunes_artist(artist_name)
    data = handle_itunes_artist_response(response, artist_name)
    if isinstance(data, dict):
        data['artist_id'] = artist_id
        save_artist_from_itunes(**{'itunes_artist_id': data['itunes_artist_id'], 'artist_id': artist_id})
        if data.get("manual_review") and not first_time:
            update_failed_artist(artist_name, artist_id, data['itunes_artist_id'], data['manual_review'])
        return data['itunes_artist_id']
    else:
        if isinstance(data, tuple):
            if first_time:
                return "try_arabic"
            else:
                update_failed_artist(artist_name, artist_id, data[0], data[1])
        elif not first_time:
            update_failed_artist(artist_name, artist_id, data)
        if not first_time:
            update_artist_status(artist_name, status="failed")

def call_and_save_track(artist_name, itunes_artist_id, artist_id):
    logger.info(f"Calling and saving tracks for artist {artist_name} with iTunes ID {itunes_artist_id}")
    response = call_itunes_tracks(itunes_artist_id)
    data = handle_itunes_track_response(response, artist_id)
    if isinstance(data, list):
        for item in data:
            save_track_from_itunes(**item)
    else:
        if isinstance(data, tuple):
            update_failed_track(problem=data[0], artist_id=artist_id, manual_review=data[1])
        else:
            update_failed_track(problem=data, artist_id=artist_id)
        update_artist_status(artist_name, status="failed")
def call_and_save_track_features():
    try:
        import essentia.standard as es
        from data_extraction.db_operations.get_features import get_urls
        import json
        logger.info(f"Fetching URLs...")
        # url_list = get_urls_from_id(artist_id)
        url_list = get_urls()
        features_list = []
        m4a_path = None
        tmp_wav = None
        for track_id, itunes_track_id, url in url_list:
            logger.info(f"Downloading track {itunes_track_id} from {url}")
            m4a_path = download_itunes_track(url)
            logger.info(f"Converting {m4a_path} to WAV")
            tmp_wav = convert_to_wav(m4a_path)
            logger.info(f"Extracting features from {tmp_wav}")
            features, features_frames = es.MusicExtractor()(tmp_wav)
            feature_dict = {}
            features_list = []
            for key in features.descriptorNames():
                val = features[key]
                # Convert numpy types to native python for JSON serialization
                if hasattr(val, 'tolist'):
                    val = val.tolist()
                feature_dict[key] = val
            features_json = json.dumps(feature_dict)
            features_list.append((features_json, track_id))
            logger.info(f"Saving features for {len(features_list)} tracks")
            save_track_features(features_list)
            logger.info(f"Saved track features for {len(features_list)} tracks")
 
    except Exception as e:
        error_message = f"Error saving track features: {e}"
        logger.error(traceback.print_exc())
        logger.error(error_message)
        return error_message
    finally:
        logger.info("Deleting temporary files...")
        if m4a_path:
            os.remove(m4a_path) if os.path.exists(m4a_path) else None
        if tmp_wav:
            os.remove(tmp_wav) if os.path.exists(tmp_wav) else None