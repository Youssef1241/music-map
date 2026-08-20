from data_extraction.utils.wrapper import call_and_save_track_features
from data_extraction.db_operations.get_features import get_tracks_with_no_features
# artists = get_tracks_with_no_features()
# for artist_id in artists:
call_and_save_track_features()