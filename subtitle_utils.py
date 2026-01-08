import pysrt

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
            content = sub.text.replace("\n", " ")
            segments.append({'start': start, 'end': end, 'text': content})
    except Exception as e:
        print(f"Error reading SRT file: {e}")
        return []
    
    return segments
        