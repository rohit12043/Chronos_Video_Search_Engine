import os
import re
import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import clipper 

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'],
)
app.mount("/static", StaticFiles(directory="templates"), name="static")

DB_NAME = "vid_database.db"

# 1. Define directories as strings
CLIPS_DIR = os.path.join("data", "clips")
THUMBNAIL_DIR = os.path.join("data", "thumbnails")

# 2. Create directories using os.makedirs
os.makedirs(CLIPS_DIR, exist_ok=True)
os.makedirs(THUMBNAIL_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return FileResponse("templates/index.html")

def get_video_path(video_id):
    with sqlite3.connect(DB_NAME) as db:
        cursor = db.cursor()
        cursor.execute("SELECT path FROM Videos where id = ?", (video_id,))
        row = cursor.fetchone()
        return row[0] if row else None
        
@app.get('/search')
def get_video_info(q: str):
    q_clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', q).strip()
    if not q_clean:
        return {"count": 0, "results": []}

    q_param = f'"{q_clean}"'
    results = []
    with sqlite3.connect(DB_NAME) as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        
        sql = """
        SELECT Videos.id as video_id, Videos.filename, Subtitles.start_time, Subtitles.end_time, Subtitles.text_content
        From Subtitles
        JOIN Videos on Subtitles.video_id = Videos.id
        JOIN Subtitles_Idx on Subtitles.id = Subtitles_Idx.rowid
        WHERE Subtitles_Idx MATCH ?
        ORDER BY rank
        LIMIT 10;
        """
        cursor.execute(sql, (q_param,))
        rows = cursor.fetchall()
        
        # Sort by start_time so search results appear in chronological order
        sorted_rows = sorted(rows, key=lambda r: r['start_time'])
        
        for r in sorted_rows:
            results.append({
                "video_id": r["video_id"],
                "filename": r["filename"],
                "start": r["start_time"],
                "end": r["end_time"],
                "text": r["text_content"]
            })
    return {"count": len(results), "results": results}

@app.get("/watch/{video_id}")
def watch_clip(video_id: int, start: float, end: float):
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