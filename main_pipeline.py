import os, ffmpeg
import indexer, database, transcriber

def get_video_metadata(file_path):
    filename = os.path.basename(file_path)
    
    try:
        res = ffmpeg.probe(file_path)
        duration = float(res['format']['duration'])
        
    except KeyError:
        print(f"Warning: Metadata missing for {filename}")
        duration = 0.0
    except ffmpeg.Error as e:
        print(f"FFmpeg Error: {e}")
        duration = 0.0
        
    return file_path, filename, duration

def run():
    database.create_tables()
    video_files = indexer.scan_directory(".")

    for video_path in video_files:
        path, name, dur = get_video_metadata(video_path)
        
        print(f"Inserting: {name} ({dur}s)")
        
        video_id = database.insert_video(path, name, dur)
        
        if not video_id:
            print("Skipping, (already in DB)")
            continue
        
        temp_audio = "temp_audio.mp3"
        try:
            print("!! Extracting & Transcribing... !!")
            segments = transcriber.extract_transcript(video_path, temp_audio)
            
            if segments:
                print(f"!! Saving  {len(segments)} subtitle lines... !!")
                database.insert_subtitles(video_id, segments)
            else:
                print("!! No dialogues detected. !!")
        except Exception as e:
            print(f"  - Error processing {name}: {e}")
                
        finally:
                if os.path.exists(temp_audio):
                    os.remove(temp_audio)

if __name__ == "__main__":
    run()