from typing import List, Tuple
import ffmpeg
from ffmpeg.nodes import FilterableStream

def overlay_images_on_background(
    background_clip: FilterableStream,
    overlays: List[Tuple[FilterableStream, float, float]]
) -> FilterableStream:
    """
    overlays: Liste von (clip, start_time, end_time)
    """
    for clip, start, end in overlays:
        background_clip = background_clip.overlay(
            clip,
            enable=f"between(t,{start},{end})",
            x="(main_w-overlay_w)/2",
            y="(main_h-overlay_h)/2",
        )
    return background_clip