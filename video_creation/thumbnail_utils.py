import textwrap
import os

from PIL import ImageFont
from pilmoji import Pilmoji
import matplotlib.font_manager as fm

from utils.fonts import getsize, getheight
from utils.console import print_step
from utils import settings


def _draw_pilmoji_text(p: Pilmoji, pos, *args, **kwargs):
    """Wrapper: Rundet Koordinaten auf int, damit PIL.Image.paste kein TypeError wirft."""
    x, y = pos
    p.text((int(round(x)), int(round(y))), *args, **kwargs)


def create_fancy_thumbnail(
    image,
    text,
    text_color,
    padding,
    wrap=35,
    font_family: str = "arial",
    font_size: int = 47,
    min_font_size: int = 24,
    left_margin: int = 120,
    right_margin: int = 120,
    vertical_offset: int = 30,
):
    """Erstellt das Titel‑PNG (inkl. farbiger Emojis via pilmoji).

    • Linksbündiger, ggf. automatisch verkleinerter Text
    • Unterstützt System‑Fonts (Fallback: Roboto‑Bold.ttf aus ./fonts)
    • Kanalname wird unten links gerendert
    """
    # ─────────────────────────────────────────── System‑/Fallback‑Font
    try:
        font_path = fm.findfont(
            fm.FontProperties(family=font_family),
            fallback_to_default=False,
        )
        base_font = ImageFont.truetype(font_path, font_size)
    except Exception:
        print_step(
            f"[yellow]Could not load system font “{font_family}” – falling back to Roboto.[/yellow]"
        )
        font_path = os.path.join("fonts", "Roboto-Bold.ttf")
        base_font = ImageFont.truetype(font_path, font_size)

    print_step(f"Creating fancy thumbnail for: {text}")

    img_w, img_h = image.size

    # ─────────────────────────────────────────── Text umbrechen & evtl. verkleinern
    lines = textwrap.wrap(text, width=wrap)
    available_w = img_w - left_margin - right_margin

    current_size = font_size
    font = base_font

    def max_line_w(f):
        return max(getsize(f, ln)[0] for ln in lines)

    while current_size > min_font_size and max_line_w(font) > available_w:
        current_size -= 1
        font = ImageFont.truetype(font_path, current_size)

    # ─────────────────────────────────────────── Vertikal positionieren
    total_h = sum(getheight(font, ln) for ln in lines) + padding * (len(lines) - 1)
    y = (img_h - total_h) / 2 + vertical_offset

    # ─────────────────────────────────────────── Kanalname‑Font
    try:
        channel_font = ImageFont.truetype(os.path.join("fonts", "Roboto-Bold.ttf"), 30)
    except Exception:
        channel_font = font  # worst‑case fallback

    # ─────────────────────────────────────────── Zeichnen (Pilmoji rendert Emojis farbig)
    with Pilmoji(image) as p:
        # Kanalname (Koordinaten int‑sicher)
        _draw_pilmoji_text(
            p,
            (205, 825),
            settings.config["settings"]["channel_name"],
            font=channel_font,
            fill=text_color,
            align="left",
        )

        # Titel‑Zeilen
        for line in lines:
            _draw_pilmoji_text(
                p,
                (left_margin, y),
                line,
                font=font,
                fill=text_color,
                align="left",
            )
            y += getheight(font, line) + padding

    return image
