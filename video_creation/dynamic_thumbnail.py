import os
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji
from utils.fonts import getheight, getsize
from utils import settings


def _draw_pilmoji_text(p: Pilmoji, pos, *args, **kwargs):
    """Wrapper: Rounds coordinates to int so PIL.Image.paste doesn't throw TypeError."""
    x, y = pos
    p.text((int(round(x)), int(round(y))), *args, **kwargs)


def parse_color(color_str):
    """Parse color string (R,G,B format) to tuple"""
    try:
        parts = [int(x.strip()) for x in color_str.split(',')]
        return tuple(parts[:3])  # Ensure only RGB, not RGBA
    except:
        return (255, 255, 255)  # Fallback to white


def create_circular_profile_image(image_path, size=80):
    """Create circular profile image from square/rectangular image"""
    try:
        # Open and resize profile image
        profile_img = Image.open(image_path)
        profile_img = profile_img.convert("RGBA")
        profile_img = profile_img.resize((size, size), Image.LANCZOS)
        
        # Create circular mask
        mask = Image.new("L", (size, size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, size, size), fill=255)
        
        # Apply mask to profile image
        circular_profile = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        circular_profile.paste(profile_img, (0, 0))
        circular_profile.putalpha(mask)
        
        return circular_profile
    except Exception as e:
        # Create fallback circular image
        fallback = Image.new("RGBA", (size, size), (100, 100, 100, 255))
        mask = Image.new("L", (size, size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, size, size), fill=255)
        fallback.putalpha(mask)
        return fallback


def create_dynamic_thumbnail(
    text,
    reddit_metrics: dict = None,
    width: int = 1080,
    corner_radius: int = 45,
    padding: int = 25
) -> Image.Image:
    """
    Create dynamic thumbnail with flexible height like comment cards
    """
    
    # Get configuration
    thumbnail_config = settings.config["settings"]["thumbnail"]
    background_color = parse_color(thumbnail_config.get("background_color", "33,33,36"))
    primary_text_color = parse_color(thumbnail_config.get("primary_text_color", "255,255,255"))
    secondary_text_color = parse_color(thumbnail_config.get("secondary_text_color", "180,180,180"))
    profile_image_path = thumbnail_config.get("profile_image_path", "assets/profile.png")
    
    # Load fonts
    try:
        channel_font = ImageFont.truetype(os.path.join("fonts", "Roboto-Bold.ttf"), 32)
        title_font = ImageFont.truetype(os.path.join("fonts", "Roboto-Bold.ttf"), 48)
        metrics_font = ImageFont.truetype(os.path.join("fonts", "Roboto-Regular.ttf"), 28)
    except OSError:
        channel_font = ImageFont.load_default()
        title_font = ImageFont.load_default()
        metrics_font = ImageFont.load_default()
    
    # Calculate content dimensions - use more aggressive space usage
    available_width = int(width - 2.5 * padding)  # Less conservative padding
    profile_size = 80
    
    # Profile + Channel name section (side by side)
    channel_name = settings.config["settings"]["channel_name"]
    profile_section_height = max(
        profile_size,  # Profile image height
        getheight(channel_font, channel_name) + getheight(metrics_font, "A") + 12  # Channel name + subreddit/author with spacing
    ) + padding // 2
    
    # Reddit metrics section (subreddit + author) - will be positioned next to profile
    subreddit_author_text = ""
    if reddit_metrics:
        show_subreddit = thumbnail_config.get("show_subreddit", True)
        show_author = thumbnail_config.get("show_author", True)
        
        reddit_info_parts = []
        if show_subreddit and reddit_metrics.get("subreddit"):
            reddit_info_parts.append(f"r/{reddit_metrics['subreddit']}")
        if show_author and reddit_metrics.get("author"):
            author_text = f"u/{reddit_metrics['author']}"
            if reddit_metrics.get("ai_rewritten", False):
                author_text += "*"
            reddit_info_parts.append(author_text)
        
        if reddit_info_parts:
            subreddit_author_text = " • ".join(reddit_info_parts)
    
    # Bottom metrics (upvotes + comments) - will be at the very bottom
    upvotes_comments_text = ""
    if reddit_metrics:
        upvotes = reddit_metrics.get("upvotes", 0)
        num_comments = reddit_metrics.get("num_comments", 0)
        
        # Format numbers (1.2k, etc.)
        if upvotes >= 1000:
            upvotes_str = f"{upvotes/1000:.1f}k" if upvotes < 10000 else f"{upvotes//1000}k"
        else:
            upvotes_str = str(upvotes)
            
        if num_comments >= 1000:
            comments_str = f"{num_comments/1000:.1f}k" if num_comments < 10000 else f"{num_comments//1000}k"
        else:
            comments_str = str(num_comments)
            
        upvotes_comments_text = f"⬆️ {upvotes_str} • 💬 {comments_str}"
    
    bottom_metrics_height = getheight(metrics_font, upvotes_comments_text) + padding if upvotes_comments_text else 0  # Normal spacing
    
    # Title section with line break preservation - USE FULL WIDTH
    char_width = getsize(title_font, "A")[0] or 15
    title_wrap_width = max(40, int(available_width // char_width * 1.3))  # Much more aggressive, like comment cards
    
    # Preserve original line breaks in title
    original_title_lines = text.split('\n')
    title_lines = []
    for original_line in original_title_lines:
        if original_line.strip():
            wrapped_lines = textwrap.wrap(original_line, width=title_wrap_width)
            title_lines.extend(wrapped_lines if wrapped_lines else [''])
        else:
            title_lines.append('')
    
    title_line_height = getheight(title_font, "A") + 12
    title_height = len(title_lines) * title_line_height + int(padding * 2.2) if title_lines else 0  # Slightly more spacing after title
    
    # Calculate total dynamic height
    total_height = int(
        padding * 2 +  # Normal top and bottom padding
        profile_section_height +  # Profile + channel name + subreddit/author
        title_height +  # Title section
        bottom_metrics_height  # Upvotes/comments at bottom
    )
    
    # Create image with calculated height
    img = Image.new("RGBA", (width, total_height), (0, 0, 0, 0))
    
    # Create rounded rectangle background
    bg_width = width - 2 * padding
    bg_height = total_height - 2 * padding
    background = Image.new("RGBA", (bg_width, bg_height), (*background_color, 255))
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
    
    # Use Pilmoji for text rendering with emoji support
    with Pilmoji(img) as p:
        current_y = padding * 2
        
        # Create and paste circular profile image
        profile_img = create_circular_profile_image(profile_image_path, profile_size)
        profile_x = padding * 2
        profile_y = current_y
        img.paste(profile_img, (profile_x, profile_y), profile_img)
        
        # Channel name (next to profile) 
        channel_x = int(profile_x + profile_size + padding // 3)
        channel_y = profile_y + 8  # Reduced offset to align nicely
        _draw_pilmoji_text(p, (channel_x, channel_y), 
                          channel_name, font=channel_font, fill=primary_text_color, align="left")
        
        # Subreddit/Author (under channel name)
        if subreddit_author_text:
            subreddit_y = channel_y + getheight(channel_font, channel_name) + 6
            _draw_pilmoji_text(p, (channel_x, subreddit_y), subreddit_author_text, 
                             font=metrics_font, fill=secondary_text_color, align="left")
        
        # Move to title section (full width, below profile section)
        current_y += profile_section_height
        
        # Title text (full width)
        for line in title_lines:
            _draw_pilmoji_text(p, (padding * 2, current_y), line, 
                             font=title_font, fill=primary_text_color, align="left")
            current_y += title_line_height
        
        # Bottom metrics (upvotes/comments) at the very bottom 
        if upvotes_comments_text:
            # Match the top spacing: add a bit more space to visually match the top
            bottom_y = total_height - int(padding * 2.5) - getheight(metrics_font, upvotes_comments_text)
            _draw_pilmoji_text(p, (padding * 2, bottom_y), upvotes_comments_text, 
                             font=metrics_font, fill=secondary_text_color, align="left")
    
    return img


def create_thumbnail_if_dynamic():
    """Create dynamic thumbnail if enabled in config, otherwise use existing system"""
    thumbnail_config = settings.config["settings"]["thumbnail"]
    if thumbnail_config.get("dynamic_height", False):
        # This would be called by the main video creation pipeline
        # For now, just return True to indicate dynamic thumbnails are enabled
        return True
    return False