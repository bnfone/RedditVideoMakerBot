from typing import List, Union
import ffmpeg
from ffmpeg.nodes import FilterableStream
from utils import settings

def merge_background_audio(audio: ffmpeg, reddit_id: str):
    """Gather an audio and merge with assets/backgrounds/background.mp3"""
    vol = settings.config["settings"]["background"]["background_audio_volume"]
    if vol == 0:
        return audio
    bg = (
        ffmpeg
        .input(f"assets/temp/{reddit_id}/background.mp3")
        .filter("volume", vol)
    )
    return ffmpeg.filter([audio, bg], "amix", duration="longest")

def concat_audio_files(
    audio_inputs: List[Union[str, FilterableStream]],
    output_path: str
):
    """
    Nimmt eine Liste von Pfaden (str) oder ffmpeg.input-Streams (FilterableStream)
    und schreibt sie zusammen in output_path.
    """
    # 1) Wenn ein Element ein Pfad ist, in einen Stream umwandeln
    streams = [
        inp if isinstance(inp, FilterableStream) else ffmpeg.input(inp)
        for inp in audio_inputs
    ]
    # 2) Zusammenfügen: nur Audio (a=1), kein Video (v=0)
    concat = ffmpeg.concat(*streams, a=1, v=0)
    # 3) In Datei schreiben
    (
        ffmpeg
        .output(
            concat,
            output_path,
            **{
                "c:a": "libmp3lame",
                "b:a": "192k",
                "ar": "24000",
                "ac": 1,
                "sample_fmt": "s16p",
            },
        )
        .overwrite_output()
        .run(quiet=True)
    )