# Arab Music Map | خريطة الموسيقى العربية

An interactive, bilingual (Arabic/English) map that visualizes similarity between Arab music artists. Audio Features are extracted directly from their most popular songs to create a matrix of their similarlities.

🔗 **Live site:** https://arabmusicmap.wiki

---

## What it does

- **Global Map** — every artist in the dataset as a node, node size reflects popularity, and each artist is linked to their top 2 most similar peers.
- **Focus Mode** — center on one artist and see their 100 closest artists by similarity, with drag-to-explore and click-to-recenter navigation.
- Fully bilingual UI (Arabic/English) with RTL-aware layout.

---

## Project structure

This project is composed of two folders: the frontend (music-map-frontend) and the data extraction pipeline (artist_data_extraction).

### 1. Frontend (music-map-frontend)
A React + Vite single-page app that renders the artist graph and search UI.

- **Framework:** React + Vite
- **Styling:** Tailwind CSS
- **Graph rendering:** [react-force-graph-2d](https://github.com/vasturiano/react-force-graph) + `d3-force`
- **Routing:** React Router
- **Deployment:** Vercel

### 2. Data pipeline (artist_data_extraction)
Data pipeline that scrapes and processes artist/song data. The most challenging part of the project was the inconsistency of data sources across the different APIs. Some music services have missing artists, others have duplicate artists, and some have missing data. To solve this, I used a combination of last.fm, musicbrainz, and itunes search APIs to pull data from multiple sources and resolve inconsistencies.

The pipeline:
1. Using a list of seed artists, we pull those artists and their top 100 most similar neighbors using last.fms [artist.getSimilar](https://www.last.fm/api/show/artist.getSimilar) API endpoint. 
2. Those artists' names and data are resolved using MusicBrainz's API, and the resulting data is stored in a DuckDB database.
3. The artists are then checked to be arab artists, and their `itunes_artist_id` is pulled using the Itunes search API. 
4. The 30 second previews of the top 5 songs of each artist are then pulled using the Itunes search API and converted to wav format for feature extraction.
5. Audio features are then extracted from the song previews using **Essentia**.  
6. Generates song/artist embeddings using **[MERT-v1-330M](https://huggingface.co/m-a-p/MERT-v1-330M)** (CC BY-NC 4.0).
7. Supplementary artist info is pulled from **Wikidata** (via SPARQL) and **Wikipedia**. 
8. The Extracted Essentia data and song embeddings are concatenated and the songs averaged for each artist to create a vector representation for each artist. The similarities are then computed using **cosine similarity**. 
9. The Output is a static similarity matrix + artist index as JSON, consumed directly by the frontend.


## Data sources & attribution

This project relies on data and models from the following sources:

- **[MusicBrainz](https://musicbrainz.org/)** — artist and recording metadata
- **[Last.fm](https://www.last.fm/)** — supplementary artist data, via the Last.fm API
- **[iTunes Search API](https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/)** — track and artwork metadata
- **[Essentia](https://essentia.upf.edu/)** — audio feature extraction
- **[MERT-v1-330M](https://huggingface.co/m-a-p/MERT-v1-330M)** by m-a-p, licensed CC BY-NC 4.0 — music understanding embeddings
- **[Wikidata](https://www.wikidata.org/)** — structured artist data via SPARQL
- **[Wikipedia](https://www.wikipedia.org/)** — supplementary artist information (CC BY-SA)



## Author

Created by **[Youssef Tarek](https://github.com/Youssef1241)**