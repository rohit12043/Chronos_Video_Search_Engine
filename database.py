import sqlite3

def create_tables():
    with sqlite3.connect("vid_database.db") as db:
        cursor = db.cursor()
        vid_table_query = '''
        CREATE TABLE IF NOT EXISTS Videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL,
            filename TEXT NOT NULL,
            duration INTEGER NOT NULL
        );
        '''
        
        cursor.execute(vid_table_query)
        
        subtitle_table_query = '''
        CREATE TABLE IF NOT EXISTS Subtitles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            start_time INTEGER NOT NULL,
            end_time INTEGER NOT NULL,
            text_content TEXT NOT NULL,
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

if __name__ == "__main__":
    create_tables()