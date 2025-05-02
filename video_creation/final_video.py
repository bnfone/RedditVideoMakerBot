import multiprocessing
import os
import re
import tempfile
import textwrap
import threading
import time
from os.path import exists  # Needs to be imported specifically
from pathlib import Path
from typing import Dict, Final, Tuple

import ffmpeg
import translators
from PIL import Image, ImageDraw, ImageFont
from rich.console import Console
from rich.progress import track

from utils import settings
from utils.cleanup import cleanup
from utils.console import print_step, print_substep
from utils.fonts import getheight
from utils.thumbnail import create_thumbnail
from utils.videos import save_data
import json

from video_creation.thumbnail_utils import create_fancy_thumbnail
from video_creation.audio_utils import merge_background_audio, concat_audio_files
from video_creation.background_utils import prepare_background
from video_creation.naming_utils import name_normalize
from video_creation.progress import ProgressFfmpeg
from video_creation.overlay_utils import overlay_images_on_background

console = Console()
def make_final_video(
    number_of_clips: int,
    length: int,
    reddit_obj: dict,
    background_config: Dict[str, Tuple],
):
    # ─────────────────────────────────────────────────────────────────────────
    # BASIC CONSTANTS
    # ─────────────────────────────────────────────────────────────────────────
    W: Final[int] = int(settings.config["settings"]["resolution_w"])
    H: Final[int] = int(settings.config["settings"]["resolution_h"])
    opacity      = settings.config["settings"]["opacity"]
    storymode    = settings.config["settings"]["storymode"]
    storymethod  = settings.config["settings"]["storymodemethod"]

    reddit_id = re.sub(r"[^\w\s-]", "", reddit_obj["thread_id"])
    title     = reddit_obj["thread_title"]

    allow_only_tts = (
        settings.config["settings"]["background"]["enable_extra_audio"]
        and settings.config["settings"]["background"]["background_audio_volume"] != 0
    )

    print_step("Creating the final video 🎥")

    # ─────────────────────────────────────────────────────────────────────────
    # BACKGROUND
    # ─────────────────────────────────────────────────────────────────────────
    background_clip = ffmpeg.input(prepare_background(reddit_id, W=W, H=H))

    # ─────────────────────────────────────────────────────────────────────────
    # AUDIO - collect → concat → (optionales) BG-Audio hinzufügen
    # ─────────────────────────────────────────────────────────────────────────
    if number_of_clips == 0 and not storymode:
        console.log("[red]No audio clips available – aborting.")
        exit()

    if storymode:
        if storymethod == 0:  # ► nur Titel + ein einziges Story-Audio
            audio_clips = [
                ffmpeg.input(f"assets/temp/{reddit_id}/mp3/title.mp3"),
                ffmpeg.input(f"assets/temp/{reddit_id}/mp3/postaudio.mp3"),
            ]
        else:                 # ► Titel + mehrere postaudio-X.mp3
            audio_clips = [
                ffmpeg.input(f"assets/temp/{reddit_id}/mp3/postaudio-{i}.mp3")
                for i in range(number_of_clips + 1)
            ]
            audio_clips.insert(0, ffmpeg.input(f"assets/temp/{reddit_id}/mp3/title.mp3"))
    else:  # ► Comment-Modus
        audio_clips = [
            ffmpeg.input(f"assets/temp/{reddit_id}/mp3/{i}.mp3") for i in range(number_of_clips)
        ]
        audio_clips.insert(0, ffmpeg.input(f"assets/temp/{reddit_id}/mp3/title.mp3"))

    concat_audio_files(audio_clips, f"assets/temp/{reddit_id}/audio.mp3")
    console.log(f"[bold green]Video will be {length} s long")

    base_audio  = ffmpeg.input(f"assets/temp/{reddit_id}/audio.mp3")
    final_audio = merge_background_audio(base_audio, reddit_id)

    # ─────────────────────────────────────────────────────────────────────────
    # IMAGES - einsammeln + Dauer-Liste erzeugen
    # ─────────────────────────────────────────────────────────────────────────
    screenshot_w = int(W * 0.45)
    image_clips: list[ffmpeg.nodes.FilterableStream] = []
    durations  : list[float] = []

    # ► Titelbild erzeugen
    title_img = create_fancy_thumbnail(Image.open("assets/title_template.png"), title, "#fff", 5)
    Path(f"assets/temp/{reddit_id}/png").mkdir(parents=True, exist_ok=True)
    title_img.save(f"assets/temp/{reddit_id}/png/title.png")
    image_clips.append(
        ffmpeg.input(f"assets/temp/{reddit_id}/png/title.png")["v"].filter("scale", screenshot_w, -1)
    )

    if storymode:
        if storymethod == 0:
            image_clips.append(
                ffmpeg.input(f"assets/temp/{reddit_id}/png/story_content.png")["v"]
                .filter("scale", screenshot_w, -1)
            )
            durations.extend([
                float(ffmpeg.probe(f"assets/temp/{reddit_id}/mp3/title.mp3")["format"]["duration"]),
                float(ffmpeg.probe(f"assets/temp/{reddit_id}/mp3/postaudio.mp3")["format"]["duration"]),
            ])
        else:
            for i in range(number_of_clips + 1):
                image_clips.append(
                    ffmpeg.input(f"assets/temp/{reddit_id}/png/img{i}.png")["v"]
                    .filter("scale", screenshot_w, -1)
                )
            durations.append(
                float(ffmpeg.probe(f"assets/temp/{reddit_id}/mp3/title.mp3")["format"]["duration"])
            )
            durations.extend(
                float(ffmpeg.probe(f"assets/temp/{reddit_id}/mp3/postaudio-{i}.mp3")["format"]["duration"])
                for i in range(number_of_clips + 1)
            )
    else:
        for i in range(number_of_clips):  # exakt vorhandene Comment-Clips
            img   = ffmpeg.input(f"assets/temp/{reddit_id}/png/comment_{i}.png")["v"].filter("scale", screenshot_w, -1)
            audio = float(ffmpeg.probe(f"assets/temp/{reddit_id}/mp3/{i}.mp3")["format"]["duration"])
            image_clips.append(img)
            durations.append(audio)
        # Titel-Dauer vorn einfügen
        durations.insert(
            0, float(ffmpeg.probe(f"assets/temp/{reddit_id}/mp3/title.mp3")["format"]["duration"])
        )

    # ─────────────────────────────────────────────────────────────────────────
    # OVERLAYS - Zeitfenster berechnen
    # ─────────────────────────────────────────────────────────────────────────
    overlays: list[tuple[ffmpeg.nodes.FilterableStream, float, float]] = []
    t = 0.0
    for idx, (clip, dur) in enumerate(zip(image_clips, durations)):
        if opacity != 1 and not storymode and idx != 0:          # Titel nie transparent
            clip = clip.filter("colorchannelmixer", aa=opacity)

        end_time = length if idx == len(image_clips) - 1 and not storymode else t + dur
        overlays.append((clip, t, end_time))
        t += dur

    background_clip = overlay_images_on_background(background_clip, overlays)

    # ─────────────────────────────────────────────────────────────────────────
    # TEXT-Overlay + Skalierung
    # ─────────────────────────────────────────────────────────────────────────
    background_clip = (
        ffmpeg.drawtext(
            background_clip,
            text=f"Background by {background_config['video'][2]}",
            x="(w-text_w)",
            y="(h-text_h)",
            fontsize=5,
            fontcolor="White",
            fontfile=os.path.join("fonts", "Roboto-Regular.ttf"),
        )
        .filter("scale", W, H)
    )

    # ─────────────────────────────────────────────────────────────────────────
    # RENDERING
    # ─────────────────────────────────────────────────────────────────────────
    print_step("Rendering the video 🎥")
    from tqdm import tqdm
    pbar = tqdm(total=100, desc="Progress: ", bar_format="{l_bar}{bar}", unit=" %")

    def _upd(p: float) -> None:
        pbar.update(round(p * 100, 2) - pbar.n)

    subreddit   = settings.config["reddit"]["thread"]["subreddit"]
    results_dir = os.path.join("results", subreddit)
    os.makedirs(results_dir, exist_ok=True)

    safe_title = name_normalize(re.sub(r"[^\w\s-]", "", title))[:251]
    file_name  = f"{safe_title}.mp4"
    main_path  = os.path.join(results_dir, file_name)

    with ProgressFfmpeg(length, _upd) as prog:
        ffmpeg.output(
            background_clip,
            final_audio,
            main_path,
            f="mp4",
            **{
                "c:v": "h264_videotoolbox",  # mac-HW-Encoder
                "b:v": "20M",
                "b:a": "192k",
                "threads": multiprocessing.cpu_count(),
            },
        ).overwrite_output().global_args("-progress", prog.output_file.name).run(quiet=True)

    pbar.update(100 - pbar.n)

    # ► Only-TTS (optional)
    if allow_only_tts:
        only_dir = os.path.join(results_dir, "OnlyTTS")
        os.makedirs(only_dir, exist_ok=True)
        with ProgressFfmpeg(length, _upd) as prog:
            ffmpeg.output(
                background_clip,
                base_audio,
                os.path.join(only_dir, file_name),
                f="mp4",
                **{
                    "c:v": "h264_videotoolbox",
                    "b:v": "20M",
                    "b:a": "192k",
                    "threads": multiprocessing.cpu_count(),
                },
            ).overwrite_output().global_args("-progress", prog.output_file.name).run(quiet=True)
        pbar.update(100 - pbar.n)

    pbar.close()

    # ─────────────────────────────────────────────────────────────────────────
    # META / CLEANUP
    # ─────────────────────────────────────────────────────────────────────────
    save_data(
        subreddit,
        file_name,
        title,
        reddit_id,
        background_config["video"][2],
        reddit_obj.get("author", ""),
        reddit_obj.get("upvotes", 0),
        reddit_obj.get("num_comments", 0),
    )

    print_step("Removing temporary files 🗑")
    print_substep(f"Removed {cleanup(reddit_id)} temporary files 🗑")
    print_step("Done! 🎉 The video is in the results folder 📁")
    print_substep(f"Video path: {main_path}")
