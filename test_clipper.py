import subprocess

input = "vid.mp4"
output = "trimmed.mp4"
start_time = "00:00:03"
duration = 10
res = subprocess.run(
    ["ffmpeg", "-ss", f"{start_time}", "-i", f"{input}",  "-t", f"{duration}", "-c", "copy", f"{output}"],
)

print(f"clip saved to {output}")