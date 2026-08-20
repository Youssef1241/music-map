#!/usr/bin/env python3
"""
wiki_popularity.py

Given an artist's name, finds their Wikipedia article and pulls monthly
pageview counts from the Wikimedia Pageviews API. Use the returned total
(or average) as a proxy for "popularity" to size nodes in a similarity map.

No API key needed. Wikimedia's Pageviews API is free, public, and has no
storage/commercial-use restrictions on the data it returns.

Usage:
    python wiki_popularity.py "Fairuz"
    python wiki_popularity.py "Fairuz" --lang ar
    python wiki_popularity.py --file artists.txt --lang en --out results.json

Requires: requests  (pip install requests)
"""

import argparse
import json
import sys
import time
from datetime import date, timedelta
from urllib.parse import quote
from data_extraction.utils.rate_limit_handling import request_with_backoff, RateLimiter
import requests

USER_AGENT = "artist-similarity-map/1.0 yussef0212@gmail.com"
HEADERS = {"User-Agent": USER_AGENT}
wikipedia_limiter = RateLimiter(calls_per_second=4)


def find_wikipedia_title(name: str, lang: str = "en") -> str | None:
    """
    Resolve a free-text artist name to a canonical Wikipedia article title
    in the given language edition, using the MediaWiki search API.
    Returns None if nothing reasonable is found.
    """
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": name,
        "format": "json",
        "srlimit": 1,
    }
    wikipedia_limiter.wait()
    resp = request_with_backoff(url, params=params, headers=HEADERS)
    # resp.raise_for_status()
    # data = resp.json()
    results = resp.get("query", {}).get("search", [])
    if not results:
        return None
    return results[0]["title"]


def get_pageviews(title: str, lang: str = "en", months_back: int = 12) -> dict:
    """
    Get daily pageviews for an article over the last `months_back` months
    from the Wikimedia REST Pageviews API, and return total + average.
    """
    end = date.today().replace(day=1) - timedelta(days=1)  # last day of prev month
    start = (end.replace(day=1) - timedelta(days=30 * (months_back - 1))).replace(day=1)

    start_str = start.strftime("%Y%m%d")
    end_str = end.strftime("%Y%m%d")

    encoded_title = quote(title.replace(" ", "_"), safe="")
    url = (
        "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
        f"{lang}.wikipedia/all-access/user/{encoded_title}/monthly/{start_str}/{end_str}"
    )

    wikipedia_limiter.wait()
    resp = request_with_backoff(url, headers=HEADERS, max_retries=5)

    # if resp.status_code == 404:
    #     # No pageview data for this article (too new, too obscure, or bad title)
    #     return {"total_views": 0, "avg_monthly_views": 0, "months_found": 0}

    # resp.raise_for_status()
    
    items = resp.get("items", [])
    total = sum(item["views"] for item in items)
    months_found = len(items)
    avg = total / months_found if months_found else 0

    return {"total_views": total, "avg_monthly_views": round(avg), "months_found": months_found}


def get_popularity(name: str, lang: str = "en", months_back: int = 12) -> dict:
    """
    Full pipeline: name -> Wikipedia title -> pageview stats.
    """
    title = find_wikipedia_title(name, lang=lang)
    if title is None:
        return {
            "query": name,
            "lang": lang,
            "title": None,
            "total_views": 0,
            "avg_monthly_views": 0,
            "months_found": 0,
            "found": False,
        }

    stats = get_pageviews(title, lang=lang, months_back=months_back)
    return {
        "query": name,
        "lang": lang,
        "title": title,
        "found": True,
        **stats,
    }


def main():
    import tqdm
    from data_extraction.db_operations.get_features import get_ids_and_names
    from data_extraction.db_operations.save_features import update_lastfm_listeners
    # parser = argparse.ArgumentParser(description="Get Wikipedia pageviews for an artist name.")
    # parser.add_argument("name", nargs="?", help="Artist name, e.g. 'Fairuz'")
    # parser.add_argument("--file", help="Path to a text file with one artist name per line")
    # parser.add_argument("--lang", default="en", help="Wikipedia language edition, e.g. en, ar, fr (default: en)")
    # parser.add_argument("--months", type=int, default=12, help="How many months of pageviews to sum (default: 12)")
    # parser.add_argument("--out", help="Path to write JSON results (default: print to stdout)")
    # parser.add_argument("--delay", type=float, default=0.2, help="Seconds to wait between requests (default: 0.2)")
    # args = parser.parse_args()

    # if not args.name and not args.file:
    #     parser.error("Provide either a name or --file")

    # names = []
    # if args.name:
    #     names.append(args.name)
    # if args.file:
    #     with open(args.file, encoding="utf-8") as f:
    #         names.extend(line.strip() for line in f if line.strip())

    # results = []
    # for n in names:
    #     try:
    #         result = get_popularity(n, lang="ar", months_back=args.months)
    #     except requests.RequestException as e:
    #         result = {"query": n, "lang": args.lang, "error": str(e), "found": False}
    #     results.append(result)
    #     print(json.dumps(result, ensure_ascii=False))
    #     time.sleep(args.delay)

    # if args.out:
    #     with open(args.out, "w", encoding="utf-8") as f:
    #         json.dump(results, f, ensure_ascii=False, indent=2)
    #     print(f"\nWrote {len(results)} results to {args.out}", file=sys.stderr)

    artists = get_ids_and_names()
    for id, name in tqdm.tqdm(artists):
        try:
            result = get_popularity(name, lang="en")
            update_lastfm_listeners(id, result['avg_monthly_views'])
        except requests.RequestException as e:
            result = {"query": name, "lang": "ar", "error": str(e), "found": False}


if __name__ == "__main__":
    main()