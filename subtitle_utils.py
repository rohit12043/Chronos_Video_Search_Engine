import pysrt
import re

def clean_tags(text):
    clean = re.sub(r'<[^>]+>', '', text)
    return clean.strip()

def format_srt_time(time_str):
    hours, minutes, rest = time_str.split(":")
    seconds, milliseconds = rest.split(",")
    total_seconds = (int(hours)*3600 + int(minutes)*60 + int(seconds) + int(milliseconds)/ 1000.0)
    return total_seconds
    
    
def parse_srt(srt_path):
    segments = []
    
    try:
        subs = pysrt.open(srt_path)
        for sub in subs:
            start = format_srt_time(str(sub.start))
            end = format_srt_time(str(sub.end))
            raw_text = sub.text.replace("\n", " ")
            content = clean_tags(raw_text)
            if content:
                segments.append({'start': start, 'end': end, 'text': content})
    except Exception as e:
        print(f"Error reading SRT file: {e}")
        return []
    
    return segments