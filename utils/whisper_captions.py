# utils/whisper_captions.py  ──  2025-05-03
# Benötigt:  pip install faster-whisper

from __future__ import annotations
from pathlib import Path
from itertools import islice
from typing  import List, Dict

from faster_whisper import WhisperModel

from utils import settings
from video_creation.caption_utils import _hex_to_ass, _ass_time, ASS_HEAD


# ═══════════════════ 1)  Audio → Wort-Timings ═══════════════════════════════════
def transcribe_words(
    audio_path   : str,
    *,
    model_size   : str   = None,         # Auto-detect aus config
    skip_seconds : float = 0.0,          # Anfangsbereich, der komplett ignoriert wird
) -> List[Dict]:
    """
    Liefert eine Liste [{word, start_time, end_time}, …].
    Wörter, deren *Ende* ≤ skip_seconds liegen, werden verworfen (Thumbnail-Titel).
    *Wichtig*: Zeiten bleiben **unverändert absolut** – kein globales Re-Timing!
    
    Optimierte Whisper-Einstellungen für bessere Transkriptionsgenauigkeit.
    """
    # Model size aus config laden falls nicht gesetzt
    if model_size is None:
        model_size = settings.config["settings"]["captions"].get("whisper_model_size", "base")
    
    # Hardware-optimierte Whisper-Konfiguration
    import platform
    import torch
    
    # Auto-detect beste Hardware-Beschleunigung
    if torch.cuda.is_available():
        device = "cuda"
        compute_type = "float16"  # NVIDIA GPU
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        device = "cpu"  # MPS nicht direkt unterstützt, aber CPU auf M1/M2 ist sehr schnell
        compute_type = "int8"   # Optimiert für Apple Silicon
    elif platform.processor() == 'arm':  # Apple Silicon
        device = "cpu"
        compute_type = "int8"   # Optimal für M1/M2/M3
    else:
        device = "cpu" 
        compute_type = "int8"   # Intel/AMD CPU
    
    model = WhisperModel(
        model_size, 
        device=device, 
        compute_type=compute_type,
        num_workers=1,                   # Konsistentere Ergebnisse
        cpu_threads=4 if device == "cpu" else 0  # Optimiert für Multi-Core
    )
    
    # Optimierte Transkriptionsparameter
    segments, _ = model.transcribe(
        audio_path, 
        word_timestamps=True,
        beam_size=5,                     # Bessere Suche (default: 5)
        temperature=0.0,                 # Deterministische Ausgabe
        compression_ratio_threshold=2.4, # Weniger aggressive Kompression
        log_prob_threshold=-1.0,         # Konservativere Token-Auswahl
        no_speech_threshold=0.6,         # Bessere Spracherkennung
        condition_on_previous_text=True, # Kontext nutzen
        vad_filter=True,                 # Voice Activity Detection
        vad_parameters=dict(
            min_silence_duration_ms=500, # Längere Pausen für bessere Segmentierung
            speech_pad_ms=400            # Mehr Padding um Sprache
        )
    )

    words: list[Dict] = []
    for seg in segments:
        for w in seg.words:
            if w.end <= skip_seconds:           # Titelteil überspringen
                continue
            
            words.append({
                "word"      : w.word.strip(),
                "start_time": w.start,          # → absolute Zeit
                "end_time"  : w.end,
            })
    return words


# ═══════════════════ 2)  Wort-Timings → ASS ═════════════════════════════════════
def build_ass_from_words(
    words    : List[Dict],
    *,
    cfg      = settings.config["settings"]["captions"],
    out_path : str = "whisper_captions.ass",
) -> str:
    """
    Erstellt eine ASS-Datei mit Highlight-Wort:
      • Fenstergröße = cfg['words_per_caption']
      • Letzte Caption bleibt sichtbar, solange die Pause < pause_threshold ist
    """
    font        = cfg["captions_font_family"]
    size        = cfg["captions_font_size"]
    color       = cfg["captions_color"]
    hlcol       = cfg["captions_highlight_color"]
    outline_px  = cfg.get("captions_outline_px", 2)
    shadow_px   = cfg.get("captions_shadow_px", 1)
    window_size = cfg.get("words_per_caption", 6)
    pause_thr   = cfg.get("pause_threshold", 1.0)
    big         = int(size * 1)

    primary   = f"&H00{_hex_to_ass(color)}"
    secondary = f"&H00{_hex_to_ass(hlcol)}"
    outline_c = "&H00000000"
    back_c    = "&H00000000"

    style = (
        f"Style: koko,{font},{size},{primary},{secondary},"
        f"{outline_c},{back_c},0,0,0,1,{outline_px},{shadow_px},5,0,0,40,1"
    )

    events: list[str] = []
    for idx, w in enumerate(words):
        # ------- Fenster bestimmen ------------------------------------------
        base   = max(0, idx - (idx % window_size))
        window = list(islice(words, base, base + window_size))

        # ------- Timings ----------------------------------------------------
        start_s = w["start_time"]

        if idx + 1 < len(words):
            next_start = words[idx + 1]["start_time"]
            if next_start - w["end_time"] <= pause_thr:
                end_s = max(start_s + 0.05, next_start)      # Caption bleibt stehen
            else:
                end_s = w["end_time"]                        # lange Pause → ausblenden
        else:
            end_s = w["end_time"]

        # ------- Text mit Highlight -----------------------------------------
        parts = []
        for tok in window:
            txt = tok["word"]
            if tok is w:
                txt = rf"{{\b1\fs{big}\c&H{_hex_to_ass(hlcol)}&}}{txt}{{\r}}"
            parts.append(txt)

        events.append(
            f"Dialogue: 0,{_ass_time(start_s)},{_ass_time(end_s)},koko,{' '.join(parts)}"
        )

    Path(out_path).write_text(
        ASS_HEAD.format(style=style) + "\n".join(events),
        encoding="utf-8",
    )
    return out_path


# ═══════════════════ 3)  Convenience-Wrapper ════════════════════════════════════
def generate_whisper_ass(
    audio_path   : str,
    *,
    reddit_id    : str,
    skip_seconds : float = 0.0,
) -> str:
    """
    Vollpipeline:   Audio → Whisper → ASS
    • skip_seconds: Titel-/Thumbnail-Dauer, wird **nur** zum Herausfiltern verwendet.
    """
    ass_file = f"assets/temp/{reddit_id}/whisper_captions.ass"
    words    = transcribe_words(audio_path, skip_seconds=skip_seconds)
    return build_ass_from_words(words, out_path=ass_file)
