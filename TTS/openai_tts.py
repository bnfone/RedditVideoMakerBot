import random
import requests
from utils import settings

class OpenAITTS:
    """
    A Text-to-Speech engine that uses OpenAI TTS API to generate audio from text.
    
    Supports all OpenAI TTS models:
    - tts-1: Fast generation, good quality (4096 char limit)
    - tts-1-hd: Highest quality, slower (4096 char limit)  
    - gpt-4o-mini-tts: Fast + high quality + instructability (2000 token/~1500 char limit)
    
    Attributes:
        max_chars (int): Base maximum characters (adjusted per model in run()).
        api_key (str): API key loaded from settings.
        api_url (str): The complete API endpoint URL, built from a base URL provided in the config.
        available_voices (list): Static list of supported voices (according to current docs).
    """
    def __init__(self):
        # Set maximum input size based on API limits 
        # (4096 characters for tts-1/tts-1-hd, 2000 tokens for gpt-4o-mini-tts)
        self.max_chars = 4096  # Will be adjusted per model in run() method
        self.api_key = settings.config["settings"]["tts"].get("openai_api_key")
        if not self.api_key:
            raise ValueError("No OpenAI API key provided in settings! Please set 'openai_api_key' in your config.")
        
        # Lese den Basis-URL aus der Konfiguration (z. B. "https://api.openai.com/v1" oder "https://api.openai.com/v1/")
        base_url = settings.config["settings"]["tts"].get("openai_api_url", "https://api.openai.com/v1")
        # Entferne ggf. den abschließenden Slash
        if base_url.endswith("/"):
            base_url = base_url[:-1]
        # Hänge den TTS-spezifischen Pfad an
        self.api_url = base_url + "/audio/speech"
        
        # Set the available voices to a static list as per OpenAI TTS documentation.
        self.available_voices = self.get_available_voices()

    def get_available_voices(self):
        """
        Return a static list of supported voices for the OpenAI TTS API.
        
        According to the documentation, supported voices include:
            "alloy", "ash", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer"
        """
        return ["alloy", "ash", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer"]

    def randomvoice(self):
        """
        Select and return a random voice from the available voices.
        """
        return random.choice(self.available_voices)

    def run(self, text, filepath, random_voice: bool = False):
        """
        Convert the provided text to speech and save the resulting audio to the specified filepath.
        
        Args:
            text (str): The input text to convert.
            filepath (str): The file path where the generated audio will be saved.
            random_voice (bool): If True, select a random voice from the available voices.
        """
        # Choose voice based on configuration or randomly if requested.
        if random_voice:
            voice = self.randomvoice()
        else:
            voice = settings.config["settings"]["tts"].get("openai_voice_name", "alloy")
            voice = str(voice).lower()  # Ensure lower-case as expected by the API

        # Select the model from configuration; default to 'tts-1'
        model = settings.config["settings"]["tts"].get("openai_model", "tts-1")
        
        # Adjust max_chars based on model
        if model == "gpt-4o-mini-tts":
            # gpt-4o-mini-tts has a 2000 token limit (roughly 1500-1600 characters)
            current_max_chars = 1500
        else:
            # tts-1 and tts-1-hd have 4096 character limit
            current_max_chars = 4096
            
        # Check if text exceeds model limit
        if len(text) > current_max_chars:
            print(f"Warning: Text length ({len(text)}) exceeds {model} limit ({current_max_chars}). Text will be truncated.")
            text = text[:current_max_chars]
        
        # Get speed from configuration; default to 1.0 (normal speed)
        speed = settings.config["settings"]["tts"].get("openai_speed", 1.0)
        
        # Validate speed range as per OpenAI API (0.25 to 4.0)
        if not (0.25 <= speed <= 4.0):
            print(f"Warning: OpenAI TTS speed {speed} is outside valid range (0.25-4.0). Using default 1.0.")
            speed = 1.0

        # Create base payload for API-request
        payload = {
            "model": model,
            "voice": voice,
            "input": text,
            "speed": speed, 
            "response_format": "mp3"  # allowed formats: "mp3", "aac", "opus", "flac", "pcm" or "wav"
        }
        
        # Add instructions for gpt-4o-mini-tts if configured
        if model == "gpt-4o-mini-tts":
            instructions = settings.config["settings"]["tts"].get("openai_instructions", "")
            if instructions and instructions.strip():
                payload["instructions"] = instructions.strip()
                print(f"Using instructions for {model}: {instructions[:50]}...")  # Show first 50 chars
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            if response.status_code != 200:
                raise RuntimeError(f"Error from TTS API: {response.status_code} {response.text}")
            # Write response as binary into file.
            with open(filepath, "wb") as f:
                f.write(response.content)
        except Exception as e:
            raise RuntimeError(f"Failed to generate audio with OpenAI TTS API: {str(e)}")