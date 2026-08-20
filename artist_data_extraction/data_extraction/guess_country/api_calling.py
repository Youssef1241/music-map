from data_extraction.utils.rate_limit_handling import request_with_backoff, RateLimiter
import requests
import os
from dotenv import load_dotenv
from loguru import logger


load_dotenv()
musicbrainz_limiter = RateLimiter(calls_per_second=0.7)
lastfm_limiter = RateLimiter(calls_per_second=3)
itunes_limiter = RateLimiter(calls_per_second=0.1)
wikipedia_limiter = RateLimiter(calls_per_second=4)

def call_lastfm(artist_name: str, get_similar_artists: bool):
    LASTFM_API_ENDPOINT = "https://ws.audioscrobbler.com/2.0/"
    LAST_FM_API_KEY = os.getenv("LAST_FM_API_KEY")
    endpoint = "artist.getSimilar" if get_similar_artists else "artist.getinfo"

    headers = {"User-Agent": "ArabMusicMap/1.0 (yussef0212@gmail.com)"}
    params = {
        "method": endpoint,
        "artist": artist_name,
        "api_key": LAST_FM_API_KEY,
        "format": "json"
    }

    lastfm_limiter.wait()
    response = request_with_backoff(LASTFM_API_ENDPOINT, params=params, headers=headers)
    return response

def call_musicbrainz_search(artist_name: str):
    MUSICBRAINZ_ENDPOINT=f"https://musicbrainz.org/ws/2/artist/"
    headers = {"User-Agent": "ArabMusicMap/1.0 (yussef0212@gmail.com)"}
    params = {
        "query": f"artist:{artist_name}",
        "fmt": "json",
        "inc": "tags+aliases",
        "limit": 5
    }
    musicbrainz_limiter.wait()
    response = request_with_backoff(MUSICBRAINZ_ENDPOINT, params=params, headers=headers)   
    return response

def call_musicbrainz(mbid: str):
    MUSICBRAINZ_ENDPOINT=f"https://musicbrainz.org/ws/2/artist/{mbid}"
    headers = {"User-Agent": "ArabMusicMap/1.0 (yussef0212@gmail.com)"}
    params = {
        "inc": "tags+aliases",
        "fmt": "json"
    }
    musicbrainz_limiter.wait()
    response = request_with_backoff(MUSICBRAINZ_ENDPOINT, params=params, headers=headers)
    return response
