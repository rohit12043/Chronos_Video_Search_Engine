import os, ffmpeg
import indexer, database, transcriber, subtitle_utils


    
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
        
    return filename, duration

def run():
    database.create_tables()
    video_files = indexer.scan_directory("./videos")

    for video_path in video_files:
        name, dur = get_video_metadata(video_path)
        
        print(f"Inserting: {name} ({dur}s)")
        
        video_id = database.insert_video(video_path, name, dur)
        
        if not video_id:
            print("Skipping, (already in DB)")
            continue
        
        temp_audio = "temp_audio.mp3"
        temp_srt = "embedded.srt"
        
        sidecar_path = os.path.splitext(video_path)[0] + ".srt"
        try:
            print("!! Processing video !!")
            segments = []
            
            if os.path.exists(sidecar_path):
                print(f"Using sidecar SRT: {os.path.basename(sidecar_path)}")
                segments = subtitle_utils.parse_srt(sidecar_path)
            
                
            else:
                srt_index = transcriber.get_text_subtitle_stream(video_path)
                if srt_index is not None and transcriber.extract_embedded_subtitles(video_path, temp_srt):
                    print(f"Using embedded subtitles: 0:s:{srt_index}")
                    segments = subtitle_utils.parse_srt(temp_srt)
                    if os.path.exists(temp_srt): os.remove(temp_srt)
                else:
                    print("No subtitles found, running Whisper model")
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