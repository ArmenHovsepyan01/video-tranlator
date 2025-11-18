import asyncio
import subprocess
from pathlib import Path
from pydub import AudioSegment

class TTSService:
    async def generate_perfectly_synced_audio(self, segments, output_path: str, voice: str = "en-US-AriaNeural"):
        combined = AudioSegment.silent(duration=0)

        for i, seg in enumerate(segments):
            text = seg["translated_text"].strip()
            if not text:
                silence = AudioSegment.silent(duration=int(seg["duration"] * 1000))
                combined += silence
                continue

            # 1. Generate normal-speed TTS
            raw_path = f"./temp/tts_raw_{i}.mp3"
            await self._edge_tts(text, voice, raw_path)

            tts_audio = AudioSegment.from_file(raw_path)
            tts_duration = len(tts_audio) / 1000.0
            target_duration = seg["duration"]

            # 2. Calculate speed factor
            if tts_duration < 0.05:  # too short, probably empty
                continue

            speed = tts_duration / target_duration

            # 3. Apply speed change with ffmpeg atempo (preserves pitch)
            adjusted_path = f"./temp/tts_adj_{i}.wav"
            self._apply_atempo_speed(raw_path, adjusted_path, speed)

            adjusted = AudioSegment.from_file(adjusted_path)

            # 4. Trim/pad to exact target duration (fixes tiny rounding errors)
            target_ms = int(target_duration * 1000)
            if len(adjusted) > target_ms:
                adjusted = adjusted[:target_ms]
            else:
                adjusted += AudioSegment.silent(duration=target_ms - len(adjusted))

            # 5. Add silence gap before this segment (if any)
            if i == 0:
                silence_before = seg["start"]
            else:
                silence_before = seg["start"] - segments[i-1]["end"]

            if silence_before > 0.02:
                combined += AudioSegment.silent(duration=int(silence_before * 1000))

            combined += adjusted

            # Cleanup
            Path(raw_path).unlink(missing_ok=True)
            Path(adjusted_path).unlink(missing_ok=True)

        # Export final perfectly synced audio
        combined.export(output_path, format="wav")

    async def _edge_tts(self, text: str, voice: str, output_path: str):
        proc = await asyncio.create_subprocess_exec(
            "edge-tts",
            "--voice", voice,
            "--text", text,
            "--write-media", output_path,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()

    def _apply_atempo_speed(self, input_path: str, output_path: str, speed: float):
        # Build safe atempo chain (atempo only allows 0.5–2.0)
        filters = []
        current = speed
        while current > 1.95:
            filters.append("atempo=2.0")
            current /= 2.0
        while current < 0.51:
            filters.append("atempo=0.5")
            current /= 0.5
        filters.append(f"atempo={current:.6f}")
        filter_str = ",".join(filters)

        subprocess.run([
            "ffmpeg", "-y", "-i", input_path,
            "-filter:a", filter_str,
            "-ar", "44100", "-ac", "2",  # ensure good quality
            output_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def get_voice_for_language(self, lang: str) -> str:
        voices = {
            "ru": "ru-RU-SvetlanaNeural",
            "en": "en-US-AriaNeural",
            "es": "es-ES-ElviraNeural",
            "fr": "fr-FR-DeniseNeural",
            "de": "de-DE-KatjaNeural",
            "hy": "hy-AM-AnahitNeural",
            # add more...
        }
        return voices.get(lang, "en-US-AriaNeural")