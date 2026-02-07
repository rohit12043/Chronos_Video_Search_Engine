import subprocess
import os

def create_clip(input_path, output_path, start_time, duration):
    start = str(start_time)
    dur = str(duration)
    
    cmd = [
        "ffmpeg", 
        "-ss", str(start_time), 
        "-i", input_path,  
        "-t", str(duration),
        "-c:v", "libx264",      
        "-preset", "ultrafast", 
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-ac", "2", 
        "-y", 
        output_path
    ]
    
    print(f"Running FFmpeg: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        print(f"FFmpeg Failed! Error logs:\n{result.stderr.decode('utf-8')}")
        return False

    return os.path.exists(output_path)