import subprocess
import whisper
import os 

input = "vid.mp4"
output = "audio.mp3"

if not os.path.isfile(output):
    subprocess.run(
        ["ffmpeg", "-i", f"{input}", "-q:a", "0", "-map", "a", f"{output}"],
    )

model = whisper.load_model("base")

res = model.transcribe(output)

print(res.get("text"))