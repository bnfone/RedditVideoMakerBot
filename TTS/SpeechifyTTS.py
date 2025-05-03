# TTS/SpeechifyTTS.py  ──  2025-05-03
"""
Speechify Text-to-Speech wrapper for RedditVideoMakerBot
Docs: https://docs.sws.speechify.com/v1/api-reference/tts/audio/speech
"""

from __future__ import annotations
import base64, json, os, random, requests
from pathlib import Path
from utils import settings
from utils.console import print_substep


class SpeechifyTTS:
    """
    • Synthetisiert Audio über  POST /v1/audio/speech
    • Schreibt rohe MP3/WAV-Bytes in `filepath`
    • Optional: cached voice-liste für Random-Voice
    """

    _VOICE_CACHE: list[dict] | None = None
    _CACHE_FILE = Path("assets/speechify_voices.json")

    def __init__(self) -> None:
        cfg = settings.config["settings"]["tts"]
        self.api_key: str = cfg["speechify_api_key"]
        if not self.api_key:
            raise ValueError("speechify_api_key missing in config.toml")

        # defaults aus Config
        self.voice_id: str   = cfg.get("speechify_voice_id", "simba")
        self.audio_fmt: str  = cfg.get("speechify_audio_format", "mp3")
        self.language: str   = cfg.get("speechify_language_code", "")
        self.model: str      = cfg.get("speechify_model", "simba-english")
        self.max_chars: int  = 20_000            # soft-limit lt. Speechify docs

        self._base_url = "https://api.sws.speechify.com/v1"

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )

    # ──────────────────────────────────────────────────────────────── public API
    def run(self, text: str, filepath: str, random_voice: bool = False) -> None:
        """
        Synthese → MP3/WAV unter `filepath`
        """
        voice = self.randomvoice() if random_voice else self.voice_id
        payload: dict = {
            "input": text,
            "voice_id": voice,
            "audio_format": self.audio_fmt,
            "model": self.model,
        }
        if self.language:
            payload["language"] = self.language

        r = self.session.post(f"{self._base_url}/audio/speech", json=payload, timeout=60)
        try:
            r.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"Speechify API error {r.status_code}: {r.text}") from e

        data = r.json()
        audio_b64 = data.get("audio_data")
        if not audio_b64:
            raise RuntimeError("Speechify response missing `audio_data`")

        with open(filepath, "wb") as f:
            f.write(base64.b64decode(audio_b64))

        # optional: Speech-marks abspeichern (<file>.json)
        if "speech_marks" in data:
            with open(f"{filepath}.json", "w", encoding="utf-8") as j:
                json.dump(data["speech_marks"], j, ensure_ascii=False)

    def randomvoice(self) -> str:
        """
        • Lädt einmalig die Voice-Liste
        • Liefert random voice_id
        """
        if SpeechifyTTS._VOICE_CACHE is None:
            SpeechifyTTS._VOICE_CACHE = self._load_voices()
        return random.choice(SpeechifyTTS._VOICE_CACHE)["voice_id"]

    # ─────────────────────────────────────────────────────────────── helpers
    def _load_voices(self) -> list[dict]:
        """
        GET /v1/voices  – Ergebnis cachen (Disk + RAM)
        """
        if self._CACHE_FILE.exists():
            with self._CACHE_FILE.open(encoding="utf-8") as f:
                return json.load(f)

        url = f"{self._base_url}/voices"
        r = self.session.get(url, timeout=30)
        r.raise_for_status()
        voices = r.json()
        self._CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._CACHE_FILE.write_text(json.dumps(voices, ensure_ascii=False), encoding="utf-8")
        print_substep(f"[Speechify] cached {len(voices)} voices", style="green")
        return voices
