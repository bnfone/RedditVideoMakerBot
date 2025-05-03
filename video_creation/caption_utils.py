# build_ass.py  ──  2025-05-03
from __future__ import annotations
import json, re, unicodedata as ud
from pathlib import Path
from utils import settings

# ═════════════════════════════════════════════ helpers ════════════════════════════════════════════
def _hex_to_ass(hexcol: str) -> str:                 # "#RRGGBB" → "BBGGRR"
    h = hexcol.lstrip("#")
    return f"{h[4:6]}{h[2:4]}{h[0:2]}"

def _ass_time(sec: float) -> str:                    # 12.34 → 0:00:12.34  (centiseconds)
    if sec < 0:                                          sec = 0.0
    cs = round(sec * 100)                                # nearest 1/100 s
    h,  rem = divmod(cs, 360000)
    m,  rem = divmod(rem,   6000)
    s,  c   = divmod(rem,    100)
    return f"{h}:{m:02d}:{s:02d}.{c:02d}"

# ═══════════════════════════════════════════ ASS header ═══════════════════════════════════════════
ASS_HEAD = """[Script Info]
ScriptType: v4.00+
Collisions: Normal
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
{style}

[Events]
Format: Layer,Start,End,Style,Text
"""

# ═════════════════════════════════════════════ builder ════════════════════════════════════════════
def build_ass(
    json_paths: list[str],
    *,
    font              : str | None = None,
    size              : int | None = None,
    color             : str | None = None,
    hlcolor           : str | None = None,
    words_per_line    : int        = 1,
    highlight_scale   : float      = 1.01,
    preroll           : float      = 0.05,       # Untertitel erscheint X s *vor* start_time
    min_display       : float      = 0.00,       # Mindest-Einblendedauer
    normalize_lead_in : bool       = False,
    gap               : float      = 0.0,        # erzwungene Stille zwischen Clips
    out_path          : str        = "captions.ass",
) -> str:
    """
    Erzeugt eine ASS-Datei, deren Timings nicht mehr driften.
    Grundprinzip:
      • Alles, was nur aus Unicode-Punctuation besteht (incl. sämtlicher Dash-Zeichen),
        wird unsichtbar – seine Dauer wird ans vorherige sichtbare Wort rangehängt.
      • Der Offset des *nächsten* Clips = tatsächliches End-Time-Stamp des letzten Dialog-Events.
        → kein Aufaddieren kleiner Kokoro-Fehler mehr.
    """

    cfg   = settings.config["settings"]["captions"]
    font  = font    or cfg["captions_font_family"]
    size  = size    or cfg["captions_font_size"]
    color = color   or cfg["captions_color"]
    hlcol = hlcolor or cfg["captions_highlight_color"]

    primary   = f"&H00{_hex_to_ass(color)}"
    secondary = f"&H00{_hex_to_ass(hlcol)}"
    outline_c = "&H00000000"
    back_c    = "&H00000000"

    style = (
        f"Style: koko,{font},{size},{primary},{secondary},"
        f"{outline_c},{back_c},0,0,0,1,2,1,5,0,0,40,1"
    )
    big = int(size * highlight_scale)

    # ----------  RegExp für reine Punctuation  ----------
    def _is_punct(word: str) -> bool:
        return all(
            (ud.category(ch).startswith("P") or ch.isspace()) for ch in word
        )

    events: list[str] = []
    cursor = 0.0                         # absoluter Zeit-Cursor der erzeugten Datei

    # ═════════════════════════════ pro Clip ═════════════════════════════
    for jp in json_paths:
        with open(jp, encoding="utf-8") as f:
            raw = json.load(f) or []

        # 1) Sichtbare Wörter + Punct-Anhängung
        words: list[dict] = []
        last: dict | None = None
        for tok in raw:
            if _is_punct(tok["word"]):
                if last is not None:
                    last["end_time"] = tok["end_time"]          # Timing beibehalten
                    last["word"] += tok["word"]                 # ← Punctuation sichtbar machen
                continue
            last = tok.copy()
            words.append(last)

        if not raw:                                             # leerer Clip
            continue

        # 2) Lead-In-Normalisierung
        lead_in = min(t["start_time"] for t in raw)
        shift   = -lead_in if (lead_in < 0 and normalize_lead_in) else 0.0

        # 3) Dialog-Events erzeugen
        clip_end = cursor                                      # wird on the fly aktualisiert
        for idx, w in enumerate(words):
            base   = (idx // words_per_line) * words_per_line
            window = words[base : base + words_per_line]

            start  = cursor + w["start_time"] + shift - preroll
            if idx + 1 < len(words):
                next_start = cursor + words[idx + 1]["start_time"] + shift - preroll
                end = max(start + min_display, next_start)
            else:
                end = cursor + w["end_time"] + shift
                if end - start < min_display:
                    end = start + min_display

            clip_end = max(clip_end, end)                     # tatsächliches Clip-Ende

            parts = []
            for token in window:
                txt = token["word"]
                if token is w:
                    txt = rf"{{\b1\fs{big}\c&H{_hex_to_ass(hlcol)}&}}{txt}{{\r}}"
                parts.append(txt)

            events.append(
                f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},koko,{' '.join(parts)}"
            )

        # 4) Cursor für nächsten Clip
        cursor = clip_end + gap

    Path(out_path).write_text(
        ASS_HEAD.format(style=style) + "\n".join(events),
        encoding="utf-8",
    )
    return out_path
