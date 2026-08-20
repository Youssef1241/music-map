from loguru import logger
from data_extraction.db_operations.get_features import get_all_names
from data_extraction.db_operations.save_features import delete_artist_from_queue, update_artist_status
from data_extraction.guess_country.utils import return_decision
from tqdm import tqdm


def handle_crawl_queue_arabs():
    logger.add("guess_country/check_artist.log", level="INFO", rotation="10 MB")
    try:
        names = get_all_names()
        deleted = 0
        skipped = 0
        review = 0
        for i, name in tqdm(enumerate(names, start = 1)):
            decision = return_decision({"name": name})
            logger.info(f"Decision for {name}: {decision}")
            if decision == "review":
                review += 1
                # update_artist_status(name, "review")
            elif decision == "delete":
                deleted += 1
                update_artist_status(name, "review")
                # delete_artist_from_queue(name)
            else:
                skipped += 1
        logger.info(f"Skipped {skipped} artists, reviewed {review} artists, deleted {deleted} artists")
        logger.info(f"Percentage of skipped artists: {skipped/len(names)*100}%")
        logger.info(f"Percentage of reviewed artists: {review/len(names)*100}%")
        logger.info(f"Percentage of deleted artists: {deleted/len(names)*100}%")
    except Exception as e:
        raise e
    finally:
        logger.info(f"Stopped at artist {name}, artist number {i}")
       


def handle_artist_table_arabs():
    import json
    import os
    from data_extraction.db_operations.get_features import get_by_id, get_all_ids
    logger.add("guess_country/check_artists_table.log", level="INFO", rotation="10 MB")
    try:
        ids = get_all_ids()
        ids = ids[1786:]
        if os.path.exists("guess_country/to_be_deleted.json"):
            with open("guess_country/to_be_deleted.json", "r") as f:
                ids_to_delete = json.load(f)
        else:
            ids_to_delete = []
        deleted = 0
        for i, id in tqdm(enumerate(ids, start = 1)):
            mbid, name = get_by_id(id)
            if mbid:
                decision = return_decision({"name": name, 'mbid': mbid})
            else:
                decision = return_decision({"name": name})
            logger.info(f"Decision for {name}: {decision}")
            if decision == "delete":
                deleted += 1
                ids_to_delete.append(id)
                # update_artist_status(name, "review")
                # delete_artist_from_queue(name)

        logger.info(f"Percentage of deleted artists: {deleted/len(ids)*100}%")
    except Exception as e:
        raise e
    finally:
        logger.info(f"Stopped at artist {id}")
        with open("guess_country/to_be_deleted.json", "w") as f:
            json.dump(ids_to_delete, f)
       
handle_artist_table_arabs()


