import subprocess
import whisper
import os 

print("Loading Whisper model...")
model = whisper.load_model("base")

def extract_transcript(video_path, audio_path):
    if not os.path.isfile(audio_path):
        print(f"Extracting audio from {video_path}...")
        subprocess.run(
            ["ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", "-y", audio_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    print(f"Transcribing {audio_path}...")
    res = model.transcribe(audio_path)

    return res['segments']