import numpy as np
import sqlite3
from sentence_transformers import SentenceTransformer
from faiss import normalize_L2

model = None
DB_NAME = "vid_database.db"

def load_model():
    """
    Load sentence embedding model
    """
    global model
    model = SentenceTransformer("all-MiniLM-L6-v2")

def generate_and_store(video_id, segments):
    """
    Generate embeddings for each subtitle and store in the database
    """
    texts = [s['text'] for s in segments]
    embeddings = model.encode(texts).astype(np.float32)

    with sqlite3.connect(DB_NAME) as db:
        cursor = db.cursor()
        cursor.execute(
            "SELECT id FROM Subtitles WHERE video_id = ? ORDER BY start_time",
            (video_id,)
        )
        subtitle_ids = [row[0] for row in cursor.fetchall()]

        updates = [
            (embeddings[i].tobytes(), subtitle_ids[i])
            for i in range(len(subtitle_ids))
        ]
        cursor.executemany(
            "UPDATE Subtitles SET embedding = ? WHERE id = ?",
            updates
        )
        db.commit()
        
def encode_text(text: str):
    """
    Encode a single query string to a normalized vector suitable for FAISS search.
    """
    if model is None:
        raise ValueError("Model not found. Call load_model() first.")
    
    vec = model.encode([text]).astype(np.float32)
    normalize_L2(vec)
    return vec
    
    