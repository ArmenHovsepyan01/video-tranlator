from gtts import gTTS
import edge_tts

voices_by_language = {
    "en": "en-GB-ThomasNeural",
    "ru": "ru-RU-DmitryNeural",
    "hy": "hy-AM-AnahitNeural",
}

class TTSService:
    def __init__(self):
        self.tts_url = "http://localhost:8080"

    def generate_speech(self, text, output_path: str, lang_code="en"):
        tts = gTTS(text, lang=lang_code, slow=False, tld='co.uk')
        tts.save(output_path)
    async def generate_speech_edge(self, text, output_path: str, lang_code="en"):
        voice = voices_by_language.get(lang_code)
        if not voice:
            raise Exception(f"There is no voice for language {lang_code}")
        communicate = edge_tts.Communicate(text, voice, rate="+50%")
        await communicate.save(output_path)