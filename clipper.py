import subprocess, os

def create_clip(input_path: str, output_path: str, start_time, duration):
    cmd = ["ffmpeg", "-ss", str(start_time), "-i", input_path,  "-t", str(duration), "-c:v", "copy", "-c:a", "aac","-ac", "2", "-y", output_path]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if os.path.exists(output_path):
        return True
    else:
        return False