import textwrap, os
from PIL import ImageDraw, ImageFont
from utils.fonts import getheight
from utils.console import print_step
from utils import settings

def create_fancy_thumbnail(image, text, text_color, padding, wrap=35):
    print_step(f"Creating fancy thumbnail for: {text}")
    font_title_size = 47
    font = ImageFont.truetype(os.path.join("fonts", "Roboto-Bold.ttf"), font_title_size)
    image_width, image_height = image.size
    lines = textwrap.wrap(text, width=wrap)
    y = (
        (image_height / 2)
        - (((getheight(font, text) + (len(lines) * padding) / len(lines)) * len(lines)) / 2)
        + 30
    )
    draw = ImageDraw.Draw(image)

    username_font = ImageFont.truetype(os.path.join("fonts", "Roboto-Bold.ttf"), 30)
    draw.text(
        (205, 825),
        settings.config["settings"]["channel_name"],
        font=username_font,
        fill=text_color,
        align="left",
    )

    if len(lines) == 3:
        lines = textwrap.wrap(text, width=wrap + 10)
        font_title_size = 40
        font = ImageFont.truetype(os.path.join("fonts", "Roboto-Bold.ttf"), font_title_size)
        y = (
            (image_height / 2)
            - (((getheight(font, text) + (len(lines) * padding) / len(lines)) * len(lines)) / 2)
            + 35
        )
    elif len(lines) == 4:
        lines = textwrap.wrap(text, width=wrap + 10)
        font_title_size = 35
        font = ImageFont.truetype(os.path.join("fonts", "Roboto-Bold.ttf"), font_title_size)
        y = (
            (image_height / 2)
            - (((getheight(font, text) + (len(lines) * padding) / len(lines)) * len(lines)) / 2)
            + 40
        )
    elif len(lines) > 4:
        lines = textwrap.wrap(text, width=wrap + 10)
        font_title_size = 30
        font = ImageFont.truetype(os.path.join("fonts", "Roboto-Bold.ttf"), font_title_size)
        y = (
            (image_height / 2)
            - (((getheight(font, text) + (len(lines) * padding) / len(lines)) * len(lines)) / 2)
            + 30
        )

    for line in lines:
        draw.text((120, y), line, font=font, fill=text_color, align="left")
        y += getheight(font, line) + padding

    return image