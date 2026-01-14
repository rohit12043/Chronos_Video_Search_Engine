import re
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import clipper 

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'],
)
DB_NAME = "vid_database.db"

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

    q = f'"{q_clean}"'
    results = []
    with sqlite3.connect(DB_NAME) as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        
        sql = """
        SELECT Videos.id as video_id, Videos.filename, Subtitles.start_time, Subtitles.text_content
        From Subtitles
        JOIN Videos on Subtitles.video_id = Videos.id
        JOIN Subtitles_Idx on Subtitles.id = Subtitles_Idx.rowid
        WHERE Subtitles_Idx MATCH ?
        ORDER BY rank
        LIMIT 50;
        """
        cursor.execute(sql, (q,))
        rows = cursor.fetchall()
        
        for r in rows:
            results.append({
                "video_id": r["video_id"],
                "filename": r["filename"],
                "start": r["start_time"],
                "text": r["text_content"]
            })
    return {"count": len(results), "results": results}

@app.get("/watch/{video_id}")
def watch_clip(video_id: int, start: float):
    video_path = get_video_path(video_id)
    if not video_path: raise HTTPException(status_code=404, detail="Video not found")
    output_filename = f"clip_{video_id}_{start}.mp4"
    
    success = clipper.create_clip(video_path, output_filename, start, 10)
    
    if success:
        return FileResponse(output_filename, media_type="video/mp4")
    else:
        raise HTTPException(status_code=500, detail="FFmpeg failed to create clip")