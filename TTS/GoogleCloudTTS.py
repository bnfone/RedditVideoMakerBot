# TTS/GoogleCloudTTS.py  ── Google Cloud Text-to-Speech Wrapper
from __future__ import annotations
import os, random
from google.cloud import texttospeech

from utils import settings

class GoogleCloudTTS:
    """Google Cloud Text-to-Speech (mp3) – kompatibel mit unserem Engine-Wrapper."""

    def __init__(self):
        self.max_chars = 5000
        self._client: texttospeech.TextToSpeechClient | None = None
        self._init_client()

    # ───────────────────────────────────────────────────────────────────────────
    #  Public API (wird vom Engine-Wrapper genutzt)
    # ───────────────────────────────────────────────────────────────────────────
    def run(self, text: str, filepath: str, random_voice: bool = False):
        """Synthesise *text* → MP3 unter *filepath*."""
        lang  = settings.config["settings"]["tts"].get("gcloud_language_code", "en-US")
        voice = (
            self._random_voice(lang)
            if random_voice else
            settings.config["settings"]["tts"].get("gcloud_voice", "en-US-Standard-A")
        )

        synth_input = texttospeech.SynthesisInput(text=text)
        voice_sel   = texttospeech.VoiceSelectionParams(
            language_code = lang,
            name          = voice
        )
        audio_conf   = texttospeech.AudioConfig(
            audio_encoding = texttospeech.AudioEncoding.MP3,
            speaking_rate  = settings.config["settings"]["tts"].get("gcloud_speed", 1.0),
        )
        response = self._client.synthesize_speech(
            input        = synth_input,
            voice        = voice_sel,
            audio_config = audio_conf,
        )

        with open(filepath, "wb") as out:
            out.write(response.audio_content)

    def randomvoice(self):
        return self._random_voice(settings.config["settings"]["tts"].get("gcloud_language_code", "en-US"))

    # ───────────────────────────────────────────────────────────────────────────
    #  Internes
    # ───────────────────────────────────────────────────────────────────────────
    def _init_client(self):
        key_path = settings.config["settings"]["tts"].get("gcloud_sa_json", "")
        if key_path and os.path.isfile(key_path):
            self._client = texttospeech.TextToSpeechClient.from_service_account_file(key_path)
        else:
            # Falls GOOGLE_APPLICATION_CREDENTIALS gesetzt ist, nutzt die Lib
            # das env-Var selbst – sonst wirft sie einen Auth-Fehler.
            self._client = texttospeech.TextToSpeechClient()

    def _random_voice(self, lang_code: str) -> str:
        """Liefert zufällig einen Voice-Name für die angegebene Sprache."""
        resp   = self._client.list_voices(language_code=lang_code)
        voices = [v.name for v in resp.voices if lang_code in v.language_codes]
        return random.choice(voices) if voices else "en-US-Standard-A"
