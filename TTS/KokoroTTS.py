import base64
import requests
from utils import settings

class KokoroTTS:
    def __init__(self):
        self.base_url     = settings.config["settings"]["tts"]["kokoro_url"]
        self.api_key      = settings.config["settings"]["tts"]["kokoro_api_key"]
        self.voice        = settings.config["settings"]["tts"]["kokoro_voice"]
        self.model        = settings.config["settings"]["tts"]["kokoro_model"]
        self.use_captioned = settings.config["settings"]["tts"].get("kokoro_captioned", False)
        self.max_chars    = 5000

    def run(self, text: str, filepath: str, random_voice: bool = False):
        if not self.api_key:
            raise ValueError("Kokoro API key is empty – please set `kokoro_api_key` in config.toml")

        endpoint = "/dev/captioned_speech" if self.use_captioned else "/v1/audio/speech"
        url = self.base_url.rstrip("/") + endpoint

        payload = {
            "model": self.model,
            "voice": self.voice,
            "input": text,
            "response_format": "mp3",
            "speed": 1.2,
        }
        if self.use_captioned:
            payload.update({
                "stream": False,
                "return_timestamps": True,
                "response_format": "mp3",
            })

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        resp = requests.post(url, json=payload, headers=headers)
        resp.raise_for_status()

        if self.use_captioned:
            # captioned endpoint returns JSON { audio: base64, timestamps: [...] }
            data = resp.json()
            audio_b64 = data.get("audio")
            if not audio_b64:
                raise RuntimeError("Kokoro captioned response missing `audio` field")
            # write MP3
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(audio_b64))
            # write timestamps JSON beside it
            with open(filepath + ".json", "w", encoding="utf-8") as jf:
                import json
                json.dump(data.get("timestamps", []), jf)
        else:
            # plain speech endpoint returns raw mp3 bytes
            with open(filepath, "wb") as f:
                f.write(resp.content)

    def randomvoice(self) -> str:
        return self.voice
