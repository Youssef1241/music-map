import os
import json
import requests
from loguru import logger
from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from db_operations import get_similar_artists_from_cache, save_to_similarity_cache

load_dotenv()

app = FastAPI(title="Arab Music Map API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
LAST_FM_API_ROOT = "https://ws.audioscrobbler.com/2.0/"
LAST_FM_API_KEY = os.getenv("LAST_FM_KEY")

@app.get("/get-similar")
async def get_similar(artist_name: str):
    if not artist_name.strip():
        return {"error": "Artist name cannot be empty"}
    logger.info(f"Artist name: {artist_name}")
    logger.info(f"Searching DB for cache on {artist_name}...")
    if (similar_artists := get_similar_artists_from_cache(artist_name)):
        logger.info(f"Found cached similar artists for {artist_name}: {similar_artists}")
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
        similar_artists = [artist['name'] for artist in parsed_response["similarartists"]['artist']][:10]
        save_to_similarity_cache(artist_name, similar_artists)

    nodes =[{"id": artist_name, "val": 20}]
    links = []

    for target in similar_artists:
        nodes.append({"id": target, "val": 10})
        links.append({"source": target, "value": 10})

    return {
        "graphData": {"nodes": nodes, "links": links}
    }
