from loguru import logger
import re
from data_extraction.utils.utils import *

def handle_lastfm_getInfo_response(response):
    data = {}    
    try:
        data['name'] = response['artist']['name']
        data['mbid'] = response['artist'].get('mbid', None)
        data['name_key'] = normalize_name(response['artist']['name'])
        data['lastfm_listeners'] = int(response['artist']['stats']['listeners'])
    except Exception as e:
        error_message = f"Error handling lastfm response: {e}, saving to failed_artists"
        logger.info(error_message)
        return error_message
    return data

def handle_lastfm_getSimilar_response(response, artist_id):
    try:
        similarity_list = [(artist_id, artist['name'], artist['match']) for artist in response["similarartists"]['artist']] 
    except Exception as e:
        error_message = f"Error getting similar artists for artist {artist_id}: {e}, saving to failed_artists"
        logger.info(error_message)
        return error_message
    return similarity_list


def handle_musicbrainz_search_response(response, artist_name):
    try:
        if response['artists'] != []:
            if response['artists'][0]['score'] < 90:
                error_message = f"No good match found for {artist_name} ({response['artists'][0]['score']} match score), saving to failed_artists"
                logger.info(error_message)
                return (error_message, True)
            else:
                data = {}
                sorted_artists = sorted(response['artists'], key=lambda artist: not is_country_arab(artist.get('country')))
                best = sorted_artists[0]

                contains_arabic = bool(re.search(r'[\u0600-\u06FF]', artist_name))
                if contains_arabic:
                    logger.info(f"Artist name '{artist_name}' contains Arabic script, looking for alias or sort-name...")
                    sort_name_contains_arabic = bool(re.search(r'[\u0600-\u06FF]', best['sort-name']))
                    if sort_name_contains_arabic:
                        if best['aliases']:
                            if (english_name :=find_arabic_name(best['aliases'])):
                                data['name_en'] = english_name
                if data.get('name_en', None) is None:
                    data['name_en'] = best['sort-name']
                country = best.get('country', None)
                area_codes = best.get('area', {}).get('iso-3166-1-codes', [])
                if response.get('tags', None) is not None:
                    tags_list = [tag['name'] for tag in response['tags']]
                else:
                    tags_list = []
        
                # if not is_arab_artist(country, area_codes, tags_list):
                #     error_message = f"Artist {artist_name} is not an Arab artist, saving to failed artists"
                #     logger.info(error_message)
                #     return (error_message, True)
                data['mbid'] = best['id']
                data['name'] = best['name']
                data['country']  = country
                data['tags']     = tags_list
                return data            
        else:
            error_message = f"No artists found for {artist_name}, saving to failed_artists"
            logger.info(error_message)
            return (error_message, True)
    except Exception as e:
        error_message = f"Error handling musicbrainz search response: {e}, saving to failed_artists"
        logger.info(error_message)
        return error_message

def handle_musicbrainz_response(response, artist_name):
    data={}
    try:
        country = response.get('country', None)
        area = response.get('area', {})
        area_codes = area.get('iso-3166-1-codes', []) if area else []
        if response.get('tags', None) is not None:
            tags_list = [tag['name'] for tag in response['tags']]
        else:
            tags_list = []
        contains_arabic = bool(re.search(r'[\u0600-\u06FF]', artist_name))
        if contains_arabic:
            logger.info(f"Artist name '{artist_name}' contains Arabic script, looking for alias or sort-name...")
            sort_name_contains_arabic = bool(re.search(r'[\u0600-\u06FF]', response['sort-name']))
            if sort_name_contains_arabic:
                if response['aliases']:
                    if (english_name :=find_arabic_name(response['aliases'])):
                        data['name_en'] = english_name
        if data.get('name_en', None) is None:
            data['name_en'] = response['sort-name']

        # if not is_arab_artist(country, area_codes, tags_list):
        #     error_message = f"Artist {artist_name} is not an Arab artist, saving to failed artists"
        #     logger.info(error_message)
        #     return (error_message, True)
        data['mbid'] = response['id']
        data['name'] = response['name'] 
        data['country'] = country
        data['tags'] = tags_list
    except Exception as e:
        error_message = f"Error handling musicbrainz response: {e}, saving to failed_artists"
        logger.info(error_message)
        return error_message
    return data

def handle_itunes_artist_response(response, artist_name):
    try:
        artist_list = [item for item in response['results'] if item['wrapperType'] == 'artist']
        if artist_list == []:
            error_message = f"No artists found for {artist_name}, saving to failed_artists"
            logger.info(error_message)
            return (error_message, True)
        else:
            closest_match = max(artist_list, key=lambda r: match_confidence(artist_name, r['artistName']))
            best_score = match_confidence(artist_name, closest_match['artistName'])
            if best_score > 0.7:
                logger.info(f"Saved artist {artist_name} with iTunes ID {closest_match['artistId']}")
                return {"itunes_artist_id": closest_match['artistId']}
            elif best_score == 0.5:
                error_message = f"Partial match found for {artist_name} ({best_score} match score), continuing but review manually"
                logger.info(error_message)
                return {"manual_review": True, "error_message": error_message, "itunes_artist_id": closest_match['artistId']}
            else:
                error_message = f"No good match found for {artist_name} ({best_score} match score), saving to failed_artists"
                logger.info(error_message)
                return (error_message, True)
    except Exception as e:
        error_message = f"Error handling itunes artist response: {e}, saving to failed_artists"
        logger.info(error_message)
        return error_message

def handle_itunes_track_response(response, artist_id):
    data=[]
    try:
        logger.info(f"Handling tracks for artist {artist_id}")
        tracks_list = [item for item in response['results'] if item['wrapperType'] == 'track']
        for item in tracks_list:
            data_item = {}
            data_item['itunes_track_id'] = item['trackId']
            data_item['name'] = item['trackName']
            data_item['preview_url'] = item['previewUrl']
            data_item['artist_id'] = artist_id
            data.append(data_item)
            logger.info(f"Processed track name: {item['trackName']}, iTunes ID {item['trackId']}") 
        if len(tracks_list) < 5:
            error_message = f"{len(tracks_list)} tracks found for {artist_id}, saving anyway"
            logger.error(error_message)
    except Exception as e:
        error_message = f"Error handling itunes artist_id: {artist_id} track response: {e}, saving to failed_tracks"
        logger.info(error_message)
        return error_message
    return data
            
def convert_to_wav(path: str):
    from pydub import AudioSegment
    audio = AudioSegment.from_file(path)
    audio.export("preview.wav", format="wav")
    return "preview.wav"