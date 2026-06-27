import os
import json
import requests
from loguru import logger
from fastapi import FastAPI
from dotenv import load_dotenv
from db_operations import get_similar_artists_from_cache, save_to_similarity_cache

load_dotenv()

app = FastAPI()
LAST_FM_API_ROOT = "https://ws.audioscrobbler.com/2.0/"
LAST_FM_API_KEY = os.getenv("LAST_FM_KEY")

@app.get("/get-similar")
async def get_similar(artist_name: str):
    logger.info(f"Artist name: {artist_name}")
    logger.info(f"Searching DB for cache on {artist_name}...")
    if (cached_similar_artists := get_similar_artists_from_cache(artist_name)):
        logger.info(f"Found cached similar artists for {artist_name}: {cached_similar_artists}")
        return {"similar_artists": cached_similar_artists}
    else:
        headers = {
            "User-Agent": "ArabMusicMap/1.0 (yussef0212@gmail.com)"
        }
        params = {
            "method": "artist.getSimilar",
            "artist": artist_name,
            "api_key": LAST_FM_API_KEY,
            "format": "json"
        }
        response = requests.get(LAST_FM_API_ROOT, params=params, headers=headers)
        parsed_response = json.loads(response.text)
        similar_artists_list = [artist['name'] for artist in parsed_response["similarartists"]['artist']][:10]

        save_to_similarity_cache(artist_name, similar_artists_list)
        return {"similar_artists": similar_artists_list}