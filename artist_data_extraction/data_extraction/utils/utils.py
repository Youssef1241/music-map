from loguru import logger
import re
import unicodedata
from typing import List
from rapidfuzz import fuzz

def normalize_name(name):
    # Lowercase, strip diacritics, remove punctuation, collapse spaces
    name = name.lower().strip()
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name)
    return name

def match_confidence(query_name, itunes_result):
    score = 0
    
    if normalize_name(itunes_result) == normalize_name(query_name):
        score = 1.0
    
    elif fuzz.token_set_ratio(query_name, itunes_result)/100 > 0.85:
        score = 0.5
    
    return score

def is_arab_artist(country: str, area_codes: List[str], tags_list: List[str]):
    ARAB_COUNTRIES = {
    'EG', 'LB', 'SA', 'AE', 'KW', 'JO', 'SY', 'IQ',
    'MA', 'DZ', 'TN', 'LY', 'SD', 'YE', 'OM', 'BH', 'QA', 'PS'
    }
    is_arab = False
    has_arab_tag = False
    if (area_codes is not None):
        is_arab = country in ARAB_COUNTRIES or any(code in ARAB_COUNTRIES for code in area_codes)
    if tags_list is not None:
        has_arab_tag = any('arab' in tag.lower() for tag in tags_list)

    return is_arab or has_arab_tag

def is_country_arab(country: str):
    ARAB_COUNTRIES = [
    'EG', 'LB', 'SA', 'AE', 'KW', 'JO', 'SY', 'IQ',
    'MA', 'DZ', 'TN', 'LY', 'SD', 'YE', 'OM', 'BH', 'QA', 'PS']

    return country in ARAB_COUNTRIES


def find_arabic_name(aliases: List[str]):
    import unicodedata
    if not aliases:
        logger.info("No aliases found for artist")
        return
    for alias in aliases:
        if alias.get("locale") == "en" and alias.get("primary") is True:
            return alias.get("name")
        
# RULE 2: Fallback if no primary 'en' flag is set (rare for famous artists)
# Check for any 'en' alias that isn't a "Search hint" typo
    for alias in aliases:
        if alias.get("locale") == "en" and alias.get("type") != "Search hint":
            return alias.get("name")

    for alias in aliases:
        # Check if the alias name is mostly Latin characters (allows accents and symbols, i.e., isn't Arabic/Hebrew/etc.)

        name = alias.get("name")
        if name:
            latin_count = sum(
                unicodedata.name(char).startswith("LATIN") 
                for char in name 
                if char.isalpha()
            )
            total_alpha = sum(1 for char in name if char.isalpha())
            # If more than 80% of letters are Latin, consider it "english/french script"
            if total_alpha > 0 and latin_count / total_alpha > 0.8:
                return name