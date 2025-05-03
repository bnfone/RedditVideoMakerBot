import textwrap, os
from PIL import ImageDraw, ImageFont
from utils.fonts import getsize, getheight
from utils.console import print_step
from utils import settings
import matplotlib.font_manager as fm

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
    """
    Render a fancy thumbnail with left-aligned text over the given image,
    shrinking the font if needed to fit horizontally.
    """
    # — 1) Try to find system font path by family name —
    try:
        font_path = fm.findfont(fm.FontProperties(family=font_family), fallback_to_default=False)
        font = ImageFont.truetype(font_path, font_size)
    except Exception:
        print_step(f"[yellow]Could not load system font “{font_family}” – falling back to Roboto.[/yellow]")
        try:
            font_path = os.path.join("fonts", "Roboto-Bold.ttf")
            font = ImageFont.truetype(font_path, font_size)
        except Exception:
            print_step("[red]❌ Could not load fallback font Roboto-Bold.ttf – exiting.[/red]")
            raise

    print_step(f"Creating fancy thumbnail for: {text}")

    draw = ImageDraw.Draw(image)
    img_w, img_h = image.size

    # — 2) Wrap text and shrink font until it fits —
    lines = textwrap.wrap(text, width=wrap)
    max_line_width = lambda f: max(getsize(f, line)[0] for line in lines)
    available_width = img_w - left_margin - right_margin
    current_size = font_size

    while current_size > min_font_size and max_line_width(font) > available_width:
        current_size -= 1
        font = ImageFont.truetype(font_path, current_size)

    # — 3) Center block vertically (+ offset) —
    total_height = sum(getheight(font, line) for line in lines)
    total_height += padding * (len(lines) - 1)
    y = (img_h - total_height) / 2 + vertical_offset

    # — 4) Draw channel name at fixed position —
    try:
        channel_font = ImageFont.truetype(os.path.join("fonts", "Roboto-Bold.ttf"), 30)
    except Exception:
        channel_font = font  # fallback if Roboto not found
    draw.text(
        (205, 825),
        settings.config["settings"]["channel_name"],
        font=channel_font,
        fill=text_color,
        align="left",
    )

    # — 5) Draw the title lines —
    for line in lines:
        draw.text((left_margin, y), line, font=font, fill=text_color, align="left")
        y += getheight(font, line) + padding

    return image
