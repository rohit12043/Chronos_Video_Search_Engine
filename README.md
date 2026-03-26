# Semantic Video Search Engine

Semantic Video Search Engine is a Python-based application designed to make video content highly accessible by indexing, transcribing, and intelligently searching through video subtitles. The application provides a responsive web interface and a robust FastAPI backend to handle end-to-end video processing, semantic search, and on-the-fly video clipping.

---

## Workflow

The following processing loop defines the core logic of the application's backend pipeline:

1. **Scan:** The indexer recursively scans directories for supported video files (`.mp4`, `.mkv`).
2. **Extract/Transcribe:** The engine extracts embedded text subtitles. If none exist, it uses the Whisper model to generate an accurate audio transcript.
3. **Embed:** Subtitle segments are converted into high-dimensional vector embeddings using the `all-MiniLM-L6-v2` SentenceTransformer model.
4. **Index:** Transcripts are stored in an SQLite database with FTS5 enabled, and vectors are indexed using FAISS for rapid semantic similarity lookups.
5. **Serve:** The FastAPI backend serves search queries, performing Hybrid Search (combining FTS and Vector scores) and generating dynamic video clips via FFmpeg.

---

## Frontend

**GUI:** Built with HTML, CSS, and vanilla JavaScript. It asynchronously queries the backend for search results and dynamically loads video clips and thumbnails, ensuring a responsive user experience without page reloads.

---

## Core Features

- **Hybrid Search Engine:** Combines the exact-match precision of SQLite Full-Text Search (FTS5) with the contextual understanding of FAISS vector search, dynamically re-ranking results.
- **Automated Transcription:** Interfaces with OpenAI's Whisper model (`tiny` by default) to transcribe dialogues when embedded subtitles are unavailable.
- **On-the-Fly Clipping:** Uses FFmpeg to generate and serve precise, padded `.mp4` video clips directly from the search results, caching them for future use.
- **Optimized Vector Embedding:** Utilizes `SentenceTransformer` to create semantic representations of dialogues, caching results to speed up repeated queries.
- **Persistent Indexing:** Stores all metadata, subtitles, and vector indices locally (`vid_database.db`, `hnsw.index`), ensuring instant startup and search capabilities across sessions.

---

## Supported Formats

The application currently supports indexing and processing the following video formats:

- MP4 (`.mp4`)
- Matroska (`.mkv`)

> **Note:** The system attempts to extract existing SRT tracks or generates its own using the Whisper model. Image-based subtitles (like PGS) are currently ignored in favor of audio transcription.

---

## Requirements

### System Requirements

- Python 3.12 or higher
- FFmpeg installed and accessible in the system PATH
- SQLite3 with FTS5 support enabled

### Python Dependencies

Install the required dependencies with:
```bash
pip install -r requirements.txt
```

Core Python packages:

- `fastapi`, `uvicorn` — Backend web server and API framework
- `sentence-transformers`, `numpy` — Vector embedding generation
- `faiss-cpu` — High-performance vector similarity search
- `whisper` — Audio transcription model
- `ffmpeg-python` — FFmpeg wrapper for processing
- `pysrt` — Subtitle parsing and manipulation

---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/rohit12043/Semantic-Video-Search-Engine.git
cd Semantic-Video-Search-Engine
```

### 2. Install FFmpeg

**Windows:** Download from [https://www.gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/) or use:
```bash
winget install ffmpeg
```

**Mac:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

### 3. Install Dependencies
```bash
python -m venv venv
```

Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

Then install packages:
```bash
pip install -r requirements.txt
```
---

## Usage Guide

### Initialize the Database

Place your video files inside a `./videos` directory in the project root, then run:
```bash
python main_pipeline.py
```

### Launch the Application
```bash
uvicorn main:app --reload
```

### Interface Usage

- **Access the Interface:** Open [http://localhost:8000](http://localhost:8000)
- **Search:** Enter keywords, phrases, or concepts
- **Playback:** Click a result to generate and play a clip
- **Pagination:** Navigate through results using controls

---

## Architecture and Database

The application uses a local SQLite database (`vid_database.db`) with:

- A **Videos** table for file metadata
- A **Subtitles** table for timestamps and vector embeddings
- A **Subtitles_Idx** virtual table using FTS5 for fast text search

---

## Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch:
```bash
git checkout -b feature/FeatureName
```

3. Commit your changes:
```bash
git commit -m "Add FeatureName"
```

4. Push to your branch:
```bash
git push origin feature/FeatureName
```

5. Open a Pull Request with a clear description
