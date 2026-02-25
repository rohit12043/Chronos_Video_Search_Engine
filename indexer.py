import os
from pathlib import Path
import sqlite3
import ffmpeg

ROOT_DIR = Path('.')
EXTENSIONS = ['.mkv', '.mp4']

def scan_directory(root_path):
    all_files = [str(f.resolve()) for f in Path(root_path).rglob('*.*') if f.suffix in EXTENSIONS]

    with sqlite3.connect("vid_database.db") as db:
        cursor = db.cursor()
        
        cursor.execute("SELECT path FROM Videos")
        existing_files = set(row[0] for row in cursor.fetchall())
        
    new_files = [f for f in all_files if f not in existing_files]
    print(f"Found {len(new_files)} new videos to process.")
    
    return new_files
    
if __name__ == "__main__":
    scan_directory(ROOT_DIR)
