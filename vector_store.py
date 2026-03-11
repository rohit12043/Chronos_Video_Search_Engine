import sqlite3

import faiss
import numpy as np

# MiniLM generates 384 dimension embeddings
DIM = 384
INDEX_FILE = "hnsw.index"
DB_NAME = "vid_database.db"

def build_index():
    """
    Build HNSW index with cosine similarity.
    """
    vectors  = []
    ids = []
    
    # Fetch all the embeddings from the Subtitle database along with subtitle id
    with sqlite3.connect("vid_database.db") as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        
        Sql = '''
        SELECT id, embedding 
        FROM Subtitles
        WHERE embedding IS NOT NULL
        '''
        
        cursor.execute(Sql)
        
        for elem in cursor.fetchall():
            subtitle_id, vector = elem
            vector = np.frombuffer(vector, dtype=np.float32)
            vectors.append(vector)
            ids.append(subtitle_id)
        ids = np.array(ids, dtype=np.int64)

    if(vectors):
        vectors = np.vstack(vectors)
        # Normalise vectors for cosine similarity
        faiss.normalize_L2(vectors)
    else:
        return None
                
    index = faiss.IndexHNSWFlat(DIM, 32, faiss.METRIC_INNER_PRODUCT)
    
    # graph construction quality (higher = better)
    index.hnsw.efConstruction = 200
    
    # Allows us to attach corresponding subtitleIDs to search the index
    index = faiss.IndexIDMap(index)
    
    index.add_with_ids(vectors, ids)
    return index
    
def save_index(index, INDEX_FILE):
    """
    Save the generated FAISS index in a file.
    """
    faiss.write_index(index, INDEX_FILE)
    
def load_index():
    """
    Load the FAISS index.
    """
    return faiss.read_index(INDEX_FILE)