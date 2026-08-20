import requests
from loguru import logger
import time

class RateLimiter:
    def __init__(self, calls_per_second):
        self.min_interval = 1.0 / calls_per_second
        self.last_called = 0
    
    def wait(self):
        elapsed = time.time() - self.last_called
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_called = time.time()


def request_with_backoff(url, params=None, headers=None, max_retries=5):
    for attempt in range(max_retries):
        r = requests.get(url, params=params, headers=headers)
        if r.status_code == 200:
            return r.json()
        elif r.status_code in (429, 503, 29, 502):
            wait_time = 4 ** (attempt+1)  # exponential backoff: 1s, 2s, 4s
            logger.warning(f"Rate limited, waiting {wait_time}s")
            time.sleep(wait_time)
        else:
            r.raise_for_status()
    raise Exception(f"Failed after {max_retries} retries: {url}")

def request_m4a_with_backoff(url, params=None, headers=None, max_retries=5):
    for attempt in range(max_retries):
        r = requests.get(url, params=params, headers=headers)
        if r.status_code == 200:
            return r
        elif r.status_code in (429, 503, 29, 502):
            wait_time = 4 ** attempt  # exponential backoff: 1s, 2s, 4s
            logger.warning(f"Rate limited, waiting {wait_time}s")
            time.sleep(wait_time)
        else:
            r.raise_for_status()
    raise Exception(f"Failed after {max_retries} retries: {url}")

