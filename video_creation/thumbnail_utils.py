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
    reddit_metrics: dict = None,
):
    """Erstellt das Titel‑PNG (inkl. farbiger Emojis via pilmoji).

    • Linksbündiger, ggf. automatisch verkleinerter Text
    • Unterstützt System‑Fonts (Fallback: Roboto‑Bold.ttf aus ./fonts)
    • Kanalname wird unten links gerendert
    """
    # ─────────────────────────────────────────── System‑/Fallback‑Font
    try:
        # Try original font name first
        font_path = fm.findfont(
            fm.FontProperties(family=font_family),
            fallback_to_default=False,
        )
        base_font = ImageFont.truetype(font_path, font_size)
    except Exception:
        font_loaded = False
        
        # If that fails and font contains hyphen, try different approaches
        if "-" in font_family:
            parts = font_family.split("-")
            font_name = parts[0]
            style = parts[1] if len(parts) > 1 else "Regular"
            
            # Try with space instead of hyphen
            try:
                font_family_alt = font_family.replace("-", " ")
                font_path = fm.findfont(
                    fm.FontProperties(family=font_family_alt),
                    fallback_to_default=False,
                )
                base_font = ImageFont.truetype(font_path, font_size)
                font_loaded = True
            except Exception:
                pass
            
            # Try with font family and weight/style properties
            if not font_loaded:
                try:
                    weight_map = {
                        "Bold": "bold", "SemiBold": "demibold", "Medium": "medium",
                        "Light": "light", "Thin": "ultralight", "Black": "heavy",
                        "ExtraBold": "ultrabold", "ExtraLight": "ultralight"
                    }
                    style_map = {
                        "Italic": "italic", "Oblique": "oblique"
                    }
                    
                    font_props = fm.FontProperties(family=font_name)
                    if style in weight_map:
                        font_props.set_weight(weight_map[style])
                    if style in style_map:
                        font_props.set_style(style_map[style])
                    
                    font_path = fm.findfont(font_props, fallback_to_default=False)
                    base_font = ImageFont.truetype(font_path, font_size)
                    font_loaded = True
                except Exception:
                    pass
        
        if not font_loaded:
            print_step(
                f"[yellow]Could not load system font \"{font_family}\" - falling back to Roboto.[/yellow]"
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

    # ─────────────────────────────────────────── Reddit Metrics Font
    try:
        metrics_font = ImageFont.truetype(os.path.join("fonts", "Roboto-Bold.ttf"), 24)
    except Exception:
        metrics_font = channel_font  # fallback

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

        # Reddit Metrics (if available)
        if reddit_metrics:
            metrics_y = 855  # Position below channel name
            subreddit = reddit_metrics.get("subreddit", "")
            author = reddit_metrics.get("author", "")
            upvotes = reddit_metrics.get("upvotes", 0)
            num_comments = reddit_metrics.get("num_comments", 0)
            ai_rewritten = reddit_metrics.get("ai_rewritten", False)
            
            # Format upvotes (e.g., 1.2k, 15k, etc.)
            if upvotes >= 1000:
                upvotes_str = f"{upvotes/1000:.1f}k" if upvotes < 10000 else f"{upvotes//1000}k"
            else:
                upvotes_str = str(upvotes)
            
            # Format comments
            if num_comments >= 1000:
                comments_str = f"{num_comments/1000:.1f}k" if num_comments < 10000 else f"{num_comments//1000}k"
            else:
                comments_str = str(num_comments)
            
            # Reddit info line - check config settings
            show_subreddit = settings.config["settings"]["thumbnail"].get("show_subreddit", True)
            show_author = settings.config["settings"]["thumbnail"].get("show_author", True)
            
            reddit_info_parts = []
            if show_subreddit and subreddit:
                reddit_info_parts.append(f"r/{subreddit}")
            if show_author and author:
                author_text = f"u/{author}"
                if ai_rewritten:
                    author_text += "*"
                reddit_info_parts.append(author_text)
            
            if reddit_info_parts:
                reddit_info = " • ".join(reddit_info_parts)
                # Use gray color for subreddit and author (readable but not white)
                gray_color = (180, 180, 180)  # Light gray - readable but distinct from white text
                _draw_pilmoji_text(
                    p,
                    (205, metrics_y),
                    reddit_info,
                    font=metrics_font,
                    fill=gray_color,
                    align="left",
                )
                metrics_y += 30
            
            # Metrics line
            metrics_text = f"⬆️ {upvotes_str} • 💬 {comments_str}"
            _draw_pilmoji_text(
                p,
                (205, metrics_y),
                metrics_text,
                font=metrics_font,
                fill=gray_color,
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
