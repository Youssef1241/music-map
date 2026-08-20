import duckdb

new_con = duckdb.connect('data_extraction/music.duckdb')

new_con.execute("""
    CREATE SEQUENCE artist_id_seq START 1;
    CREATE SEQUENCE track_id_seq START 1;

    CREATE TABLE artists (
        id INTEGER PRIMARY KEY DEFAULT nextval('artist_id_seq'),
        mbid TEXT,
        itunes_artist_id TEXT,
        name_key TEXT,
        name TEXT,
        country TEXT,
        lastfm_listeners INTEGER,
        tags VARCHAR[],
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        name_en TEXT
    );

    CREATE TABLE tracks (
        id INTEGER PRIMARY KEY DEFAULT nextval('track_id_seq'),
        artist_id INTEGER REFERENCES artists(id),
        itunes_track_id BIGINT,
        name TEXT,
        preview_url TEXT,
        raw_features_json JSON
    );

    CREATE TABLE artist_similarity_lastfm (
        artist_id INTEGER REFERENCES artists(id),
        similar_artist_name TEXT,
        lastfm_score REAL,
        PRIMARY KEY (artist_id, similar_artist_name)
    );


    CREATE TABLE failed_artists (
        artist_name TEXT,
        artist_id INTEGER REFERENCES artists(id),
        problem TEXT,
        failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        manual_review BOOLEAN DEFAULT FALSE
    );

    CREATE TABLE failed_tracks (
        track_name TEXT,
        artist_id INTEGER REFERENCES artists(id),
        track_id INTEGER REFERENCES tracks(id),
        problem TEXT,
        failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        manual_review BOOLEAN DEFAULT FALSE
    );

    CREATE TABLE artist_queue (
        artist_name VARCHAR PRIMARY KEY,
        status VARCHAR,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        lastfm_listeners INTEGER
    );
""")

# new_con.execute("ATTACH 'music_old.db' AS old_db")

# # Order matters: parents before children (FK dependencies)
# new_con.execute("SELECT setval('artist_id_seq', (SELECT MAX(id) FROM old_db.artists))")
# new_con.execute("INSERT INTO artists SELECT * FROM old_db.artists")

# new_con.execute("SELECT setval('track_id_seq', (SELECT MAX(id) FROM old_db.tracks))")
# new_con.execute("INSERT INTO tracks SELECT * FROM old_db.tracks")

# new_con.execute("INSERT INTO artist_similarity_lastfm SELECT * FROM old_db.artist_similarity_lastfm")
# new_con.execute("INSERT INTO crawl_queue SELECT * FROM old_db.crawl_queue")
# new_con.execute("INSERT INTO failed_artists SELECT * FROM old_db.failed_artists")
# new_con.execute("INSERT INTO failed_tracks SELECT * FROM old_db.failed_tracks")
# new_con.execute("INSERT INTO artist_queue SELECT * FROM old_db.artist_queue")

# new_con.execute("DETACH old_db")
new_con.close()