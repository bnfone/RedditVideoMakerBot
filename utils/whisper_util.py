import whisper

def transcribe_audio(audio_path, max_words=5):
    """
    Transcribe the audio file using Whisper and return a list of subtitle segments.
    
    Each segment is a dictionary with 'start', 'end', and 'text' keys.
    The 'text' value is limited to the first max_words words.
    """
    model = whisper.load_model("base")  # Load the Whisper base model for a good speed/accuracy trade-off.
    result = model.transcribe(audio_path)
    segments = []
    for seg in result["segments"]:
        # Limit text to the first max_words words.
        words = seg["text"].strip().split()
        subtitle_text = " ".join(words[:max_words])
        segments.append({
            "start": seg["start"],
            "end": seg["end"],
            "text": subtitle_text
        })
    return segments
