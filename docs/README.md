# Reddit Video Maker Bot Documentation

## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [Architecture](#architecture)
7. [Text-to-Speech Engines](#text-to-speech-engines)
8. [Video Creation Pipeline](#video-creation-pipeline)
9. [AI Rewriting System](#ai-rewriting-system)
10. [Customization](#customization)
11. [Troubleshooting](#troubleshooting)
12. [Advanced Usage](#advanced-usage)
13. [API Reference](#api-reference)

## Overview

The **Reddit Video Maker Bot** is a sophisticated automation tool that transforms Reddit posts and comments into engaging TikTok-style videos. The bot fetches content from Reddit, optionally rewrites it using AI, generates text-to-speech narration, creates dynamic visual cards, and assembles everything into polished short-form videos.

### Key Capabilities
- **Multi-platform TTS Support**: 10+ different text-to-speech engines
- **Dynamic Visual Generation**: Comment cards and thumbnails without browser dependencies
- **AI Content Enhancement**: OpenAI-powered content rewriting for better engagement
- **Story Mode**: Single-narrator video creation from Reddit stories
- **Multi-language Support**: Translation and localization capabilities
- **Automated Workflow**: Complete video generation from Reddit post to final MP4

## Features

### Core Features
- **Dynamic Comment Cards**: Browser-free visual generation using PIL/Pilmoji
- **Dynamic Thumbnails**: Configurable, auto-sizing thumbnail generation
- **Multi-TTS Engine Support**: TikTok, ElevenLabs, OpenAI, Kokoro, AWS Polly, and more
- **AI Story Rewriting**: Transform Reddit content for target audiences
- **Background Media**: Automatic video/audio background selection
- **Whisper Captions**: Word-level timing with customizable styling
- **Watermarking**: Configurable brand watermarks
- **Batch Processing**: Process multiple posts in sequence

### Advanced Features
- **Story Mode**: Convert long Reddit posts into single-narrator videos
- **Content Filtering**: NSFW filtering, comment length limits, minimum engagement thresholds
- **Font Customization**: Multiple font families and sizing options
- **Color Theming**: Fully customizable color schemes for cards and thumbnails
- **Profile Integration**: Channel branding with profile images and names
- **Emoji Support**: Full emoji rendering in text and titles

## Installation

### Prerequisites
- **Python 3.10 or 3.11** (strictly enforced)
- **FFmpeg** (automatically installed if missing)
- **Virtual Environment** (recommended)

### Step-by-Step Setup

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd RedditVideoMakerBot
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuration Setup**
   ```bash
   cp utils/.config.template.toml config.toml
   ```

5. **Edit Configuration**
   Edit `config.toml` with your Reddit credentials and preferences.

### Dependencies Overview
- **Core**: `moviepy`, `praw`, `pillow`, `pilmoji`
- **TTS Engines**: `elevenlabs`, `boto3`, `openai`, `gTTS`
- **Media Processing**: `ffmpeg-python`, `whisper`
- **Utilities**: `rich`, `toml`, `requests`

## Configuration

The bot uses TOML configuration files with a comprehensive template system. The main configuration sections are:

### Reddit API Configuration
```toml
[reddit.creds]
client_id = "your_reddit_client_id"
client_secret = "your_reddit_client_secret"
username = "your_reddit_username"
password = "your_reddit_password"
2fa = false

[reddit.thread]
subreddit = "AskReddit"
post_id = ""  # Leave empty for random posts
random = true
max_comment_length = 500
min_comments = 20
```

### TTS Configuration
```toml
[settings.tts]
voice_choice = "elevenlabs"  # Options: tiktok, elevenlabs, openai, kokoro, aws_polly, etc.
elevenlabs_api_key = "your_elevenlabs_key"
openai_api_key = "your_openai_key"
silence_duration = 0.0
no_emojis = false
```

### Visual Settings
```toml
[settings.thumbnail]
dynamic_height = true
background_color = "33,33,36"
primary_text_color = "255,255,255"
secondary_text_color = "180,180,180"
profile_image_path = "assets/profile.jpg"
show_subreddit = true
show_author = true

[settings.captions]
captions_font_family = "Sigmar"
captions_font_size = 85
captions_color = "FFFFFF"
words_per_caption = 4
caption_mode = "whisper"
```

### AI Rewriter Configuration
```toml
[settings.rewriter]
enabled = true
api_endpoint = "https://api.openai.com/v1"
model = "gpt-4"
target_group = "Gen-Z (16-22), queer/questioning audience"
generate_caption = true
```

## Usage

### Basic Usage
```bash
# Run with default config
python main.py

# Run with custom config
python main.py --config config.custom.toml

# Test TTS voices
python ptt.py

# Launch web GUI
python GUI.py
```

### Command Line Options
- `--config` or `-c`: Specify alternative configuration file
- Default configuration file: `config.toml`

### Batch Processing
Set `times_to_run` in your configuration:
```toml
[settings]
times_to_run = 5  # Generate 5 videos
```

### Specific Post Processing
Set a specific post ID:
```toml
[reddit.thread]
post_id = "abc123"  # Process this specific post
```

## Architecture

### Core Pipeline Flow
1. **Reddit Data Fetching** (`reddit/subreddit.py`)
   - Fetches posts and comments using PRAW
   - Filters by length, score, and content requirements
   - Extracts metadata (author, upvotes, timestamps)

2. **Optional AI Rewriting** (`utils/rewriter.py`)
   - Transforms content for target audiences
   - Maintains original meaning while improving engagement
   - Generates social media captions

3. **Text-to-Speech Generation** (`video_creation/voices.py`)
   - Supports 10+ TTS engines
   - Handles text preprocessing and cleanup
   - Generates timing data for captions

4. **Visual Asset Creation**
   - **Comment Cards** (`video_creation/comment_card_renderer.py`)
     - Dynamic height calculation
     - Emoji rendering with Pilmoji
     - Rounded corners and custom theming
   - **Thumbnails** (`video_creation/dynamic_thumbnail.py`)
     - Profile integration
     - Configurable layouts and colors
     - Auto-sizing based on content

5. **Background Media** (`video_creation/background.py`)
   - Video and audio background selection
   - Media duration matching
   - Volume balancing

6. **Final Assembly** (`video_creation/final_video.py`)
   - Combines all assets using MoviePy
   - Adds captions with word-level timing
   - Applies watermarks and effects

### Directory Structure
```
RedditVideoMakerBot/
├── main.py                 # Entry point
├── GUI.py                  # Web interface
├── config*.toml           # Configuration files
├── TTS/                   # Text-to-speech engines
│   ├── elevenlabs.py
│   ├── openai_tts.py
│   ├── kokoro.py
│   └── ...
├── video_creation/        # Video processing pipeline
│   ├── comment_card_renderer.py
│   ├── dynamic_thumbnail.py
│   ├── voices.py
│   ├── final_video.py
│   └── background.py
├── reddit/               # Reddit API handling
│   └── subreddit.py
├── utils/                # Shared utilities
│   ├── settings.py
│   ├── rewriter.py
│   ├── fonts.py
│   └── cleanup.py
├── assets/               # Media assets
│   ├── temp/            # Temporary files
│   ├── backgrounds/     # Background videos
│   └── templates/       # Thumbnail templates
├── fonts/               # Font files
└── results/            # Generated videos
```

## Text-to-Speech Engines

### Supported Engines

#### 1. ElevenLabs
```toml
voice_choice = "elevenlabs"
elevenlabs_api_key = "your_api_key"
elevenlabs_voice_name = "Laura"
```
- **Pros**: Highest quality, realistic voices
- **Cons**: Requires API credits

#### 2. OpenAI TTS
```toml
voice_choice = "openai"
openai_api_key = "your_api_key"
openai_voice_name = "alloy"
openai_model = "tts-1-hd"
```
- **Pros**: Good quality, reliable
- **Cons**: Requires API credits

#### 3. TikTok TTS
```toml
voice_choice = "tiktok"
tiktok_sessionid = "your_session_id"
tiktok_voice = "en_us_001"
```
- **Pros**: Authentic TikTok sound
- **Cons**: Requires session ID extraction

#### 4. Kokoro TTS (Local)
```toml
voice_choice = "kokoro"
kokoro_url = "http://localhost:8880"
kokoro_voice = "am_fenrir+am_puck+af_heart"
```
- **Pros**: Free, local processing
- **Cons**: Requires local server setup

#### 5. AWS Polly
```toml
voice_choice = "polly"
aws_polly_voice = "Matthew"
```
- **Pros**: Enterprise-grade reliability
- **Cons**: Requires AWS credentials

### Voice Selection Tips
- **For viral content**: Use TikTok voices
- **For professional content**: Use ElevenLabs or OpenAI
- **For cost-effective processing**: Use Kokoro or AWS Polly
- **For multilingual content**: Use Google Cloud TTS

## Video Creation Pipeline

### Comment Card Generation

The comment card system creates visually appealing cards without browser dependencies:

```python
def create_comment_card(
    comment_data: dict,
    reddit_obj: dict = None,
    width: int = 1080,
    background_color: tuple = (33, 33, 36, 255),
    corner_radius: int = 20,
    padding: int = 40
) -> Image.Image
```

**Features:**
- Dynamic height calculation based on content
- Text wrapping with line break preservation
- Emoji support via Pilmoji
- Configurable colors and styling
- Author names and upvote counts

### Dynamic Thumbnail System

Creates thumbnails that adapt to content length:

```python
def create_dynamic_thumbnail(
    text: str,
    reddit_metrics: dict = None,
    width: int = 1080,
    corner_radius: int = 25
) -> Image.Image
```

**Components:**
- Circular profile images
- Channel name and branding
- Subreddit and author information
- Dynamic text sizing
- Upvote and comment metrics

### Background Integration

Automatic background selection and processing:

- **Video backgrounds**: Minecraft, gaming footage, abstract visuals
- **Audio backgrounds**: Lo-fi, ambient music
- **Duration matching**: Automatically crops to match content length
- **Volume balancing**: Ensures narration is clearly audible

## AI Rewriting System

### Purpose
The AI rewriter transforms Reddit content to better suit target audiences and increase engagement potential.

### Configuration
```toml
[settings.rewriter]
enabled = true
model = "gpt-4"
target_group = "Gen-Z (16-22), LGBTQ+ friendly audience"
system_prompt = "You are a content adapter for social media..."
```

### Rewriting Process
1. **Content Analysis**: Examines original post structure and tone
2. **Audience Adaptation**: Adjusts language for target demographic
3. **Engagement Optimization**: Adds hooks and calls-to-action
4. **Length Optimization**: Ensures content fits video duration requirements
5. **Caption Generation**: Creates social media captions with hashtags

### Output Format
```json
{
    "hook": "Mind-blowing story from Reddit...",
    "body": "Adapted story content...",
    "caption": "Caption with hashtags #viral #reddit"
}
```

## Customization

### Font Customization
Place font files in the `fonts/` directory:
- `Roboto-Bold.ttf` - For headlines and author names
- `Roboto-Regular.ttf` - For body text
- `Sigmar-Regular.ttf` - For captions (optional)

### Color Schemes
Customize colors in configuration:
```toml
[settings.thumbnail]
background_color = "33,33,36"        # Dark gray
primary_text_color = "255,255,255"   # White
secondary_text_color = "180,180,180" # Light gray
```

### Background Media
Add custom backgrounds to `assets/backgrounds/`:
- Videos: MP4 format, 1080x1920 resolution recommended
- Audio: MP3 format, moderate tempo recommended

### Profile Branding
Set custom profile images and channel information:
```toml
[settings]
channel_name = "YourChannel"

[settings.thumbnail]
profile_image_path = "assets/your_profile.jpg"
```

## Troubleshooting

### Common Issues

#### 1. Import Errors
**Problem**: `ModuleNotFoundError` when running
**Solution**: 
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

#### 2. Reddit API Authentication
**Problem**: Invalid credentials error
**Solution**: 
- Verify Reddit app credentials
- Check username/password
- Ensure 2FA setting matches account

#### 3. TTS API Issues
**Problem**: TTS generation fails
**Solution**:
- Verify API keys are valid
- Check API quotas and billing
- Test with different TTS engine

#### 4. Font Loading Errors
**Problem**: Font files not found
**Solution**:
- Ensure fonts exist in `fonts/` directory
- Check file permissions
- Verify font file formats (TTF/OTF)

#### 5. FFmpeg Issues
**Problem**: Video processing fails
**Solution**:
- Run `python main.py` to auto-install FFmpeg
- Manually install FFmpeg system-wide
- Check PATH environment variable

### Debug Mode
Enable detailed logging by modifying the script:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Optimization
- Use smaller comment limits for faster processing
- Choose lightweight TTS engines for batch processing
- Reduce video resolution for testing
- Use local TTS servers (Kokoro) to avoid API rate limits

## Advanced Usage

### Custom TTS Engines
Create new TTS engines by implementing the base interface:

```python
class CustomTTSEngine:
    def __init__(self):
        pass
    
    def run(self, text: str, filepath: str, random_voice: bool = False):
        # Implementation here
        pass
```

### Webhook Integration
Set up webhooks for automated processing:
```python
# Example webhook endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    post_id = data.get('post_id')
    main(post_id)
    return {'status': 'success'}
```

### Batch Configuration
Process multiple posts with different settings:
```toml
[reddit.thread]
post_id = "post1+post2+post3"  # Process multiple posts
```

### Custom Filters
Implement content filters:
```python
def custom_filter(comment):
    # Custom filtering logic
    if len(comment['body']) < 50:
        return False
    return True
```

## API Reference

### Core Functions

#### `main(POST_ID=None)`
Main processing function
- `POST_ID`: Optional specific Reddit post ID
- **Returns**: None (generates video files)

#### `generate_comment_cards(reddit_obj, output_dir, card_count=None)`
Generate visual comment cards
- `reddit_obj`: Reddit data object
- `output_dir`: Output directory for PNG files
- `card_count`: Limit number of cards generated

#### `create_dynamic_thumbnail(text, reddit_metrics=None, width=1080)`
Create dynamic thumbnail images
- `text`: Title text for thumbnail
- `reddit_metrics`: Engagement metrics (upvotes, comments)
- `width`: Thumbnail width in pixels

### Configuration API

#### `settings.config`
Global configuration object loaded from TOML files

#### `settings.check_toml(template_path, config_path)`
Validate configuration against template
- **Returns**: Boolean indicating validity

### Utility Functions

#### `cleanup(reddit_id)`
Clean up temporary files for specific Reddit post

#### `id(reddit_object)`
Generate unique identifier for Reddit content

#### `print_step(message)` / `print_substep(message)`
Console output formatting functions

---

## Contributing

### Development Setup
1. Fork the repository
2. Create feature branch
3. Follow existing code style
4. Add tests for new features
5. Submit pull request

### Code Style
- Use type hints where possible
- Follow PEP 8 conventions
- Add docstrings to public functions
- Keep functions focused and modular

### Testing
Run tests with:
```bash
python -m pytest tests/
```

---

## License

This project is open source. Please check the LICENSE file for specific terms.

---

## Support

For issues and support:
1. Check this documentation
2. Review existing GitHub issues
3. Join the Discord community
4. Submit detailed bug reports

**Project Repository**: [GitHub Link]
**Documentation**: This file
**Community**: [Discord Link]