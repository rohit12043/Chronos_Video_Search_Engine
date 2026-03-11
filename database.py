import os
import sqlite3

DB_NAME = "vid_database.db"

def create_tables():
    """
    Create the Videos and Subtitles tables with FTS triggers.
    """
    with sqlite3.connect(DB_NAME) as db:
        cursor = db.cursor()
        vid_table_query = '''
        CREATE TABLE IF NOT EXISTS Videos (
            id INTEGER PRIMARY KEY,
            path TEXT NOT NULL,
            filename TEXT NOT NULL,
            duration REAL NOT NULL
        );
        '''
        
        cursor.execute(vid_table_query)
        
        subtitle_table_query = '''
        CREATE TABLE IF NOT EXISTS Subtitles (
            id INTEGER PRIMARY KEY,
            video_id INTEGER NOT NULL,
            start_time REAL NOT NULL,
            end_time REAL NOT NULL,
            text_content TEXT NOT NULL,
            embedding BLOB,
            FOREIGN KEY (video_id) REFERENCES Videos(id)
        );
        '''
        
        cursor.execute(subtitle_table_query)
        
        # FTS virtual table for text search
        cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS Subtitles_Idx 
        USING fts5(text_content);
        ''')
        
        cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS after_subtitle_insert
        AFTER INSERT ON Subtitles
        BEGIN
        INSERT INTO Subtitles_IDX(rowid, text_content)
        VALUES(new.id, new.text_content);
        END;
        ''')
        
        print("Database initialized with FTS Triggers.")

def insert_video(path, filename, duration):
    """
    Insert a video record into the database and return its ID.
    """
    with sqlite3.connect(DB_NAME) as db:
        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO Videos (path, filename, duration) VALUES (?, ?, ?)", (path, filename, duration))
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
        
    
def insert_subtitles(video_id, segments):
    """
    Insert subtitle segments for a given video into the database.
    """
    data = []
    for s in segments:
        data.append((video_id, s['start'], s['end'], s['text'].strip()))
        
    with sqlite3.connect(DB_NAME) as db:
        cursor = db.cursor()
        cursor.executemany("INSERT INTO Subtitles (video_id, start_time, end_time, text_content) VALUES (?, ?, ?, ?)", data)

if __name__ == "__main__":
    if os.path.exists(DB_NAME):
        print("Removing old database schema...")
        os.remove(DB_NAME)
        
    create_tables()