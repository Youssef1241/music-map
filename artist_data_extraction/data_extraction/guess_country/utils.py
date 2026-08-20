
from data_extraction.utils.api_calls import call_musicbrainz, call_musicbrainz_search
import re
from data_extraction.guess_country.wikipedia import get_artist_nationality


ARAB_COUNTRY_CODES = {
    'DZ', 'BH', 'KM', 'DJ', 'EG', 'IQ', 'JO', 'KW', 'LB', 'LY',
    'MR', 'MA', 'OM', 'PS', 'QA', 'SA', 'SO', 'SD', 'SY', 'TN',
    'AE', 'YE'
}

ARAB_COUNTRY_NAMES = {
    'Algeria', 'Bahrain', 'Comoros', 'Djibouti', 'Egypt', 'Iraq',
    'Jordan', 'Kuwait', 'Lebanon', 'Libya', 'Mauritania', 'Morocco',
    'Oman', 'Palestine', 'Qatar', 'Saudi Arabia', 'Somalia', 'Sudan',
    'Syria', 'Tunisia', 'United Arab Emirates', 'Yemen'
}

ARAB_NATIONALITIES = {
    'algerian', 'bahraini', 'comorian', 'djiboutian', 'egyptian', 'iraqi',
    'jordanian', 'kuwaiti', 'lebanese', 'libyan', 'mauritanian', 'moroccan',
    'omani', 'palestinian', 'qatari', 'saudi', 'somali', 'sudanese',
    'syrian', 'tunisian', 'emirati', 'yemeni'
}

def flatten_values(d):
    if isinstance(d, dict):
        return [y for v in d.values() for y in flatten_values(v)]
    elif isinstance(d, list):
        return [y for i in d for y in flatten_values(i)]
    else:
        return [str(d)]

def is_musicbrainz_arab(response):
        ARAB_COUNTRIES = {
            'EG', 'LB', 'SA', 'AE', 'KW', 'JO', 'SY', 'IQ',
            'MA', 'DZ', 'TN', 'LY', 'SD', 'YE', 'OM', 'BH', 'QA', 'PS'
        }
        flattened = [value.lower()for value in flatten_values(response)]
        
        if any(country.lower() in flattened for country in ARAB_COUNTRIES):
            return True

        flat_str = "$".join(flattened)

        if any(nationality.lower() in flat_str for nationality in ARAB_NATIONALITIES):
            return True

        if any(country.lower() in flat_str for country in ARAB_COUNTRY_NAMES):
            return True
     
        return False
 
def find_top_artist(response):
    sorted_artists = sorted(response['artists'], key=lambda artist: not is_musicbrainz_arab(artist))
    if sorted_artists:
        if sorted_artists[0]['score'] >= 90:
            return sorted_artists[0]
    

def is_arab_artist(data):
    if data.get('mbid'):
        response = call_musicbrainz(data['mbid'])
        if is_musicbrainz_arab(response):
            return True
    else:
        response = call_musicbrainz_search(data['name'])
        artist = find_top_artist(response)
        if artist:
            if is_musicbrainz_arab(artist):
                return True

    contains_arabic = bool(re.search(r'[\u0600-\u06FF]', data['name']))
    lang = 'ar' if contains_arabic else 'en'
    nationalities = get_artist_nationality(data['name'], lang)
    if any([nationality['is_arab_country'] for nationality in nationalities]):
        return True
    


    return False

def return_decision(data):
    contains_arabic = bool(re.search(r'[\u0600-\u06FF]', data['name']))
    if contains_arabic:
        return "skipc"
    is_arab = is_arab_artist(data)
    if is_arab:
        return "skip"
    if (not is_arab) and contains_arabic:
        return "review"
    else:
        return "delete"

