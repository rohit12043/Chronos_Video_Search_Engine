import os
import re
import sqlite3
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import numpy as np
import clipper
import embedder 
import faiss

# Global variables
DB_NAME = "vid_database.db"
CLIPS_DIR = os.path.join("data", "clips")
THUMBNAIL_DIR = os.path.join("data", "thumbnails")
INDEX_FILE = "hnsw.index"
faiss_index: faiss.Index = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Load embedder model and FAISS index, and clear old clips on startup.
    """
    embedder.load_model()
    print("Embedder loaded.")
    
    global faiss_index
    if os.path.exists(INDEX_FILE):
        faiss_index = faiss.read_index(INDEX_FILE)
        print("FAISS index loaded successfully")
    else:
        print("FAISS index not found, vector search unavailable")
        
    print("Server starting: performing initial file cleanup...")
    # Clear the clips on startup
    if os.path.exists(CLIPS_DIR):
        for file in os.listdir(CLIPS_DIR):
            file_path = os.path.join(CLIPS_DIR, file)

            if os.path.isfile(file_path) and file.endswith(".mp4"):
                try:
                    os.remove(file_path)
                    print(f"Removed file: {file}")
                except OSError as e:
                    print(f"Error removing file: {e}")
                            
    # Ensure directory exists
    os.makedirs(CLIPS_DIR, exist_ok=True)
    os.makedirs(THUMBNAIL_DIR, exist_ok=True)
    
    yield
    print("Server shutting down...")
    
app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'],
)
app.mount("/static", StaticFiles(directory="templates"), name="static")
DB_NAME = "vid_database.db"

@app.get("/")
def read_root():
    """
    Serve the main HTML page.
    """
    return FileResponse("templates/index.html")

def get_video_path(video_id):
    """
    Return filesystem path for a given video ID.
    """
    with sqlite3.connect(DB_NAME) as db:
        cursor = db.cursor()
        cursor.execute("SELECT path FROM Videos where id = ?", (video_id,))
        row = cursor.fetchone()
        return row[0] if row else None
        
@app.get('/search')
def get_video_info(q: str, page_no: int):
    """
    Search subtitles with FTS and return paginated results.
    """
    q_clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', q).strip()
    if not q_clean:
        return {"count": 0, "results": []}

    total_count = 0
    offset = page_no*10
    q_param = f'"{q_clean}"'
    results = []
    
    # For first page of results, calculate total count of matches
    if(page_no == 0):
        with sqlite3.connect(DB_NAME) as db:
            db.row_factory = sqlite3.Row
            cursor = db.cursor()
            
            sql = """
            SELECT COUNT(*) From Subtitles
            JOIN Videos on Subtitles.video_id = Videos.id
            JOIN Subtitles_Idx on Subtitles.id = Subtitles_Idx.rowid
            WHERE Subtitles_Idx MATCH ?
            ORDER BY rank, Subtitles.id
            """
            cursor.execute(sql, (q_param,))
            total_count = cursor.fetchone()[0]

    # Fetch subtitle along with video information (name and id)
    with sqlite3.connect(DB_NAME) as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        
        sql = """
        SELECT Videos.id as video_id,
            Videos.filename,
            Subtitles.start_time,
            Subtitles.end_time,
            highlight(Subtitles_Idx, 0, '<span class="highlight"><b>', '</b></span>') AS text_content
        FROM Subtitles
        JOIN Videos on Subtitles.video_id = Videos.id
        JOIN Subtitles_Idx on Subtitles.id = Subtitles_Idx.rowid
        WHERE Subtitles_Idx MATCH ?
        ORDER BY rank, Subtitles.id
        LIMIT 10 OFFSET ?
        """
        cursor.execute(sql, (q_param, offset))
        rows = cursor.fetchall()
        
        
        for r in rows:
            results.append({
                "video_id": r["video_id"],
                "filename": r["filename"],
                "start": r["start_time"],
                "end": r["end_time"],
                "text": r["text_content"]
            })
            
    return {
        "total_count": total_count if page_no == 0 else None,
        "page_size": 10,
        "results": results
    }

@app.get("/vector_search")
def vector_search(q: str, top_k: int = 100, page_no: int = 0, page_size: int = 10):
    """
    Search FAISS vector index for semantically similar subtitles.
    """
    global faiss_index
    if faiss_index is None:
        raise HTTPException(status_code=503, detail="Vector index not loaded")
    
    q_vec = embedder.encode_text(q)
    
    vector_scores, vector_ids = faiss_index.search(q_vec, top_k)
    
    results = []
    with sqlite3.connect(DB_NAME) as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        
        # 3️⃣ Fetch subtitle and video information for each result
        for i in range(len(vector_ids[0])):
            sub_id = int(vector_ids[0][i])
            score = float(vector_scores[0][i])
            
            cursor.execute("""
                SELECT Subtitles.*, Videos.filename, Videos.id AS video_id
                FROM Subtitles
                JOIN Videos ON Subtitles.video_id = Videos.id
                WHERE Subtitles.id = ?
            """, (sub_id,))
            
            row = cursor.fetchone()
            if row:
                results.append({
                    "video_id": row["video_id"],
                    "filename": row["filename"],
                    "start": row["start_time"],
                    "end": row["end_time"],
                    "text": row["text_content"],
                    "score": score
                })
    
    total = len(results)
    paginated = results[page_no * page_size : (page_no + 1) * page_size]
    
    return {
        "total_count": total,
        "page_size": page_size,
        "results": paginated
    }

@app.get("/hybrid_search")
def hybrid_search(q: str, top_k: int = 100, alpha: float = 0.5, page_no: int = 0, page_size: int = 10):
    """
    Hybrid search endpoint: combines FTS + vector search using hybrid_rerank.
    alpha: weight of FTS vs vector (0=only vector, 1=only FTS)
    """
    results = hybrid_rerank(q, top_k=top_k, alpha=alpha, page_no=page_no, page_size=page_size)
    return results

def hybrid_rerank(q: str, top_k: int = 100, alpha: float = 0.5, page_no: int = 0, page_size: int = 10):
    """
    perfrom hybrid search: FTS candidate retrieval + FAISS semantic reranking.
    alpha: weight of FTS vs vector similarity (0=only vector, 1=only FTS)
    """
    global faiss_index
    if faiss_index is None:
        raise RuntimeError("Vector index not loaded")
    

    q_clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', q).strip()
    if not q_clean:
        return{"total_count": 0, "page_size": 10, "results": []}
    
    fts_query = f'"{q_clean}"'
    
    # FTS Search
    with sqlite3.connect(DB_NAME) as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        
        sql = """
        SELECT Subtitles.id, Videos.id as video_id,
            Videos.filename,
            Subtitles.start_time,
            Subtitles.end_time,
            highlight(Subtitles_Idx, 0, '<span class="highlight"><b>', '</b></span>') AS text_content
        FROM Subtitles
        JOIN Videos on Subtitles.video_id = Videos.id
        JOIN Subtitles_Idx on Subtitles.id = Subtitles_Idx.rowid
        WHERE Subtitles_Idx MATCH ?
        """
        
        cursor.execute(sql, (fts_query, ))
        fts_rows = cursor.fetchall()
        
     # Vector Search
    q_vec = embedder.encode_text(q)
    
    vector_scores, vector_ids = faiss_index.search(q_vec, top_k)
    
    # Create dict mappings for scores and ids
    fts_dict = {row['id']: 1.0/(i+1) for i, row in enumerate(fts_rows)}
    vector_dict = {int(vector_ids[0][i]): float(vector_scores[0][i]) for i in range(len(vector_ids[0]))}
    
    combined = {}
    
    # Merge all candidate ids (unique)
    all_ids = set(fts_dict.keys()) | set(vector_dict.keys())
    
    # Combined scores based on the formula: alpha*(fts_scores) + (1-alpha)*(vector_scores)
    for _id_ in all_ids:
        combined[_id_] = alpha*fts_dict.get(_id_, 0.0) + (1-alpha)*vector_dict.get(_id_, 0.0)
    
    top_results = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    results = []
    
    with sqlite3.connect(DB_NAME) as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        
        for sub_id, score in top_results:
            sql = """
            SELECT Subtitles.*, Videos.filename, Videos.id as video_id
            FROM Subtitles Join Videos on Subtitles.video_id=Videos.id
            WHERE Subtitles.id = ?
            """
            cursor.execute(sql, (sub_id, ))
            
            row = cursor.fetchone()
            
            if row:
                results.append({
                "video_id": row["video_id"],
                "filename": row["filename"],
                "start": row["start_time"],
                "end": row["end_time"],
                "text": row["text_content"],
                "score": score
                })
    
    total = len(results)
    paginated = results[page_no * page_size : (page_no + 1) * page_size]
    
    return {
        "total_count": total,
        "page_size": page_size,
        "results": paginated
    }
    
@app.get("/watch/{video_id}")
def watch_clip(video_id: int, start: float, end: float):
    """
    Generate or serve cached video clip for given time interval.
    """
    video_path = get_video_path(video_id)
    if not video_path: 
        raise HTTPException(status_code=404, detail="Video not found")

    start_padded = max(0, start - 0.5)
    end_padded = end + 1.0 
    duration = max(4.0, end_padded - start_padded)

    output_filename = f"clip_{video_id}_{start_padded:.2f}_{end_padded:.2f}.mp4"
    # 3. Join paths using os.path.join
    output_path = os.path.join(CLIPS_DIR, output_filename)

    if not os.path.exists(output_path):
        print(f"Generating new clip: {output_filename}") 
        success = clipper.create_clip(video_path, output_path, start_padded, duration)
        if not success:
            raise HTTPException(status_code=500, detail="FFmpeg failed")
    else:
        print(f"Serving cached clip: {output_filename}")
    
    return FileResponse(output_path, media_type="video/mp4")

@app.get("/thumbnail/{video_id}")
def get_thumbnail(video_id: int, time: float):
    """
    Generate or serve cached thumbnail image at given time.
    """
    vid_path = get_video_path(video_id)
    if not vid_path: 
        raise HTTPException(status_code=404, detail="Video not found")
        
    thumb_filename = f"thumb_{video_id}_{time:.2f}.jpg"
    # 4. Join paths using os.path.join
    thumb_filepath = os.path.join(THUMBNAIL_DIR, thumb_filename)
    
    if not os.path.exists(thumb_filepath):
        print(f"Generating thumbnail: {thumb_filename}")
        success = clipper.generate_thumbnail(vid_path, thumb_filepath, time)
    
        if not success:
            raise HTTPException(status_code=500, detail="Thumbnail generation failed.")    
    else:
        print(f"Serving cached thumbnail: {thumb_filename}")
        
    return FileResponse(thumb_filepath, media_type="image/jpeg")