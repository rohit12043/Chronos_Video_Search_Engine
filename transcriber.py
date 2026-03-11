import subprocess
import whisper
import os 
import ffmpeg

model = None

def load_model():
    """
    Load Whisper transcription model.
    """
    global model
    model = whisper.load_model("tiny")
    
def get_text_subtitle_stream(file_path):
    """
    Return index of first text subtitle stream or None.
    """
    try:
        probe = ffmpeg.probe(file_path)
        subtitle_stream_idx = 0
        
        for stream in probe['streams']:
            if(stream['codec_type']  == 'subtitle'):
                codec = stream.get('codec_name', '').lower()
                if codec in ['hdmv_pgs_subtitle', 'dvd_subtitle']:
                    subtitle_stream_idx += 1
                    print("Ignoring image-based subtitles.")
                    continue
                return subtitle_stream_idx
        return None
    except Exception as e:
        print(f"Subtitle probe failed: {e}")
        return None
    
def extract_embedded_subtitles(video_path, output_srt_path):
    """
    Extract embedded text subtitles to SRT file.
    """
    srt_index = get_text_subtitle_stream(video_path)
    if srt_index is None:
        return False
    
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-map", f"0:s:{srt_index}","-c:s", "srt", output_srt_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return os.path.exists(output_srt_path)
        
def extract_transcript(video_path, audio_path):
    """
    Transcribe audio file into text segments.
    """
    if not os.path.isfile(audio_path):
        print(f"Extracting audio from {video_path}...")
        subprocess.run(
            ["ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", "-y", audio_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    print(f"Transcribing {audio_path}...")
    res = model.transcribe(audio_path, fp16=False)

    return res['segments']