from data_extraction.utils.rate_limit_handling import request_with_backoff, RateLimiter

WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"

# A minimal list of Arab countries (Wikidata Q-IDs) to check citizenship against.
# You can expand this list as needed.
ARAB_COUNTRY_QIDS = {
    "Q79": "Egypt",
    "Q822": "Lebanon",
    "Q796": "Iraq",
    "Q858": "Syria",
    "Q810": "Jordan",
    "Q878": "United Arab Emirates",
    "Q846": "Qatar",
    "Q851": "Saudi Arabia",
    "Q1016": "Libya",
    "Q948": "Tunisia",
    "Q262": "Algeria",
    "Q1028": "Morocco",
    "Q1049": "Sudan",
    "Q398": "Bahrain",
    "Q790": "Kuwait",
    "Q1020": "Somalia",  # Arab League member, optional
    "Q958": "Mauritania",  # Arab League member, optional
    "Q233": "Palestine",
    "Q334": "Comoros",  # Arab League member, optional
    "Q977": "Djibouti",  # Arab League member, optional
    "Q1006": "Oman",
}

wikipedia_limiter = RateLimiter(calls_per_second=4)
def get_artist_nationality(artist_name: str, lang: str = None):
    """
    Query Wikidata for an artist's country of citizenship (P27) and
    native language (P103).

    If `lang` is given (e.g. "ar" or "en"), matches the label in that
    specific language. If `lang` is None, matches the name against a
    label in ANY language, which is what you want when passing
    an Arabic name and you're not sure whether it's stored as an
    Arabic-script label vs. only as an alias.
    """
    if lang:
        label_clause = f'?artist rdfs:label "{artist_name}"@{lang}.'
    else:
        # Match label in any language (handles Arabic-script names
        # regardless of which language tag Wikidata stored it under)
        label_clause = f'''
      ?artist rdfs:label ?anyLabel.
      FILTER(STR(?anyLabel) = "{artist_name}")
        '''

    query = f"""
    SELECT ?artist ?artistLabel ?country ?countryLabel ?nativeLang ?nativeLangLabel WHERE {{
      {label_clause}
      ?artist wdt:P106 ?occupation.
      VALUES ?occupation {{ wd:Q639669 wd:Q177220 wd:Q36834 wd:Q855091 }} # musician, singer, composer, singer-songwriter
      OPTIONAL {{ ?artist wdt:P27 ?country. }}
      OPTIONAL {{ ?artist wdt:P103 ?nativeLang. }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,ar". }}
    }}
    LIMIT 5
    """

    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": "ArabMusicMap/1.0 (yussef0212@gmail.com)"
    }
    wikipedia_limiter.wait()
    data = request_with_backoff(WIKIDATA_SPARQL_URL, params={"query": query}, headers=headers)

    results = []
    for row in data["results"]["bindings"]:
        artist_uri = row.get("artist", {}).get("value", "")
        artist_qid = artist_uri.split("/")[-1] if artist_uri else None
        country_uri = row.get("country", {}).get("value", "")
        country_qid = country_uri.split("/")[-1] if country_uri else None
        country_label = row.get("countryLabel", {}).get("value")

        is_arab = country_qid in ARAB_COUNTRY_QIDS

        results.append({
            "artist_qid": artist_qid,
            "artist_label": row.get("artistLabel", {}).get("value"),
            "country_qid": country_qid,
            "country_label": country_label,
            "is_arab_country": is_arab,
        })

    return results
print(get_artist_nationality("French Montana", "en"))