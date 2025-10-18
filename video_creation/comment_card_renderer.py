import os
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji
from rich.progress import track
from utils.fonts import getheight, getsize
from TTS.engine_wrapper import process_text
from utils import settings




def _draw_pilmoji_text(p: Pilmoji, pos, *args, **kwargs):
    """Wrapper: Rundet Koordinaten auf int, damit PIL.Image.paste kein TypeError wirft."""
    x, y = pos
    p.text((int(round(x)), int(round(y))), *args, **kwargs)


def parse_color(color_str):
    """Parse color string (R,G,B format) to tuple"""
    try:
        parts = [int(x.strip()) for x in color_str.split(',')]
        return tuple(parts[:3])  # Ensure only RGB, not RGBA
    except:
        return (255, 255, 255)  # Fallback to white


def create_comment_card(
    comment_data: dict,
    reddit_obj: dict = None,
    width: int = 1080,  # Match config resolution
    background_color: tuple = None,  # Will be read from config
    text_color: tuple = (240, 240, 240, 255),     # Light text
    author_color: tuple = (255, 255, 255, 255),   # White for author (prominent)
    upvote_color: tuple = (255, 140, 0, 255),     # Orange for upvotes
    title_color: tuple = (150, 150, 150, 255),    # Gray for post title
    corner_radius: int = 45,  # Match thumbnail radius
    padding: int = 25  # Match thumbnail padding
) -> Image.Image:
    """
    Create a comment card with dynamic height, rounded corners, dark background
    
    Args:
        comment_data: Dict with 'comment_body', 'comment_author', 'comment_score'
        reddit_obj: Reddit object for post title
        width: Card width
        background_color: RGBA tuple for background
        text_color: RGBA tuple for main text
        author_color: RGBA tuple for author name
        upvote_color: RGBA tuple for upvote count
        title_color: RGBA tuple for post title
        corner_radius: Radius for rounded corners
        padding: Internal padding
    """
    
    # Get configuration colors to match thumbnail
    thumbnail_config = settings.config["settings"]["thumbnail"]
    if background_color is None:
        bg_color_rgb = parse_color(thumbnail_config.get("background_color", "33,33,36"))
        background_color = (*bg_color_rgb, 255)  # Add alpha channel
    
    primary_text_color = parse_color(thumbnail_config.get("primary_text_color", "255,255,255"))
    secondary_text_color = parse_color(thumbnail_config.get("secondary_text_color", "180,180,180"))
    
    # Load fonts with proper sizing
    try:
        title_font = ImageFont.truetype(os.path.join("fonts", "Roboto-Regular.ttf"), 28)  # Smaller, less prominent
        author_font = ImageFont.truetype(os.path.join("fonts", "Roboto-Bold.ttf"), 36)     # Prominent author
        text_font = ImageFont.truetype(os.path.join("fonts", "Roboto-Regular.ttf"), 40)
        upvote_font = ImageFont.truetype(os.path.join("fonts", "Roboto-Regular.ttf"), 28)  # Match thumbnail metrics font
        
        # Note: Emoji handling is done via Pilmoji, no separate emoji font needed
            
    except OSError:
        # Fallback to default font
        title_font = ImageFont.load_default()
        author_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        upvote_font = ImageFont.load_default()
    
    # Calculate content dimensions first - use more aggressive space usage
    available_width = width - 3 * padding  # Less conservative padding
    
    # Post title with subreddit (if available)
    title_height = 0
    title_lines = []
    if reddit_obj and reddit_obj.get('thread_title'):
        subreddit = reddit_obj.get('subreddit', 'reddit')
        title_text = f"in r/{subreddit}: {reddit_obj['thread_title']}"
        # Use full width for title as well - more aggressive
        title_char_width = getsize(title_font, "A")[0] or 15
        title_wrap_width = max(60, int(available_width // title_char_width * 1.2))  # More characters per line
        
        # Limit title to one line with ellipsis if too long
        if len(title_text) > title_wrap_width:
            title_text = title_text[:title_wrap_width-3] + "..."
        title_lines = [title_text]
        title_line_height = getheight(title_font, "A") + 8  # Smaller spacing
        title_height = len(title_lines) * title_line_height + padding // 2  # Less padding
    
    # Author name
    author_text = f"u/{comment_data.get('comment_author', 'Unknown')}"
    author_height = getheight(author_font, author_text) + padding // 2
    
    # Main comment text (don't process_text to keep emojis!)
    comment_text = comment_data.get('comment_body', '')
    # Calculate wrap width more accurately to use full available space - aggressive
    char_width = getsize(text_font, "A")[0] or 15
    text_wrap_width = max(50, int(available_width // char_width * 1.3))  # Much more characters per line
    
    # Preserve original line breaks by splitting first, then wrapping each line
    original_lines = comment_text.split('\n')
    text_lines = []
    for original_line in original_lines:
        if original_line.strip():  # If line has content
            wrapped_lines = textwrap.wrap(original_line, width=text_wrap_width)
            text_lines.extend(wrapped_lines if wrapped_lines else [''])  # Keep empty lines
        else:  # Empty line - preserve it
            text_lines.append('')
    text_line_height = getheight(text_font, "A") + 12
    content_height = len(text_lines) * text_line_height
    
    # Upvote section
    upvote_height = getheight(upvote_font, "⬆️ 999 upvotes") + padding // 2
    
    # Calculate total dynamic height with extra spacing for upvotes
    total_height = (
        padding * 3 +  # Top, middle spacings, bottom
        title_height +
        author_height +
        content_height +
        padding +      # Extra space before upvotes
        upvote_height +
        padding // 2   # Extra bottom padding
    )
    
    # Create image with calculated height
    img = Image.new("RGBA", (width, total_height), (0, 0, 0, 0))
    
    # Create rounded rectangle background
    bg_width = width - 2 * padding
    bg_height = total_height - 2 * padding
    background = Image.new("RGBA", (bg_width, bg_height), background_color)
    mask = Image.new("L", (bg_width, bg_height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        [(0, 0), (bg_width, bg_height)], 
        radius=corner_radius, 
        fill=255
    )
    
    # Apply mask to background
    background.putalpha(mask)
    img.paste(background, (padding, padding), background)
    
    # Use Pilmoji for proper emoji rendering like fancy_thumbnail
    with Pilmoji(img) as p:
        current_y = padding * 2
        
        # Draw post title (if available) - left aligned
        if title_lines:
            for line in title_lines:
                _draw_pilmoji_text(p, (padding * 2, current_y), line, font=title_font, fill=title_color, align="left")
                current_y += title_line_height
            current_y += padding // 3  # Less space after title
        
        # Draw author name
        _draw_pilmoji_text(p, (padding * 2, current_y), author_text, font=author_font, fill=author_color, align="left")
        current_y += author_height
        
        # Draw main comment text - left aligned
        for line in text_lines:
            _draw_pilmoji_text(p, (padding * 2, current_y), line, font=text_font, fill=text_color, align="left")
            current_y += text_line_height
        
        # Draw upvote count (bottom left) - using same style as thumbnail
        upvotes = comment_data.get('comment_score', 0)
        # Format upvotes like in thumbnail
        if upvotes >= 1000:
            upvotes_str = f"{upvotes/1000:.1f}k" if upvotes < 10000 else f"{upvotes//1000}k"
        else:
            upvotes_str = str(upvotes)
        upvote_text = f"⬆️ {upvotes_str}"  # Only emoji and number, no "upvotes" text
        upvote_y = total_height - int(padding * 2.5) - getheight(upvote_font, upvote_text)  # Match thumbnail spacing
        _draw_pilmoji_text(p, (padding * 2, upvote_y), upvote_text, font=upvote_font, fill=secondary_text_color, align="left")
    
    return img


def generate_comment_cards(reddit_obj: dict, output_dir: str, card_count: int = None) -> None:
    """
    Generate comment cards for all comments in reddit object
    
    Args:
        reddit_obj: Reddit object with comments
        output_dir: Directory to save PNG files
        card_count: Limit number of cards (None for all)
    """
    
    comments = reddit_obj.get("comments", [])
    if card_count:
        comments = comments[:card_count]
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Create title card
    title_data = {
        'comment_body': reddit_obj.get('thread_title', ''),
        'comment_author': reddit_obj.get('author', ''),
        'comment_score': reddit_obj.get('upvotes', 0)
    }
    
    title_card = create_comment_card(title_data, reddit_obj)
    title_card.save(f"{output_dir}/title.png")
    
    # Create comment cards
    for idx, comment in track(enumerate(comments), description="Generating comment cards"):
        card = create_comment_card(comment, reddit_obj)
        card.save(f"{output_dir}/comment_{idx}.png")