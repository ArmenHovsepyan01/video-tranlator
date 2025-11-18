from fastapi import APIRouter, HTTPException, File, status, UploadFile
from pathlib import Path
import shutil
from services import VideoService, TranslationService, TranscriptionService, TTSService

router = APIRouter(prefix="/video", tags=["Video"])

translation_service = TranslationService()
video_service = VideoService()
transcription_service = TranscriptionService()
tts_service = TTSService()

@router.post("/upload", status_code=status.HTTP_200_OK)
async def upload_video(file: UploadFile = File(...), target_language: str = "ru"):  # "ru" for Russian
    upload_dir = Path("./uploads")
    temp_dir = Path("./temp")
    output_dir = Path("./outputs")

    for d in [upload_dir, temp_dir, output_dir]:
        d.mkdir(exist_ok=True)

    video_path = upload_dir / file.filename
    with open(video_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        # 1. Extract clean WAV audio (16kHz is best for Whisper)
        audio_path = temp_dir / "original_audio.wav"
        video_service.extract_audio_from_video(str(video_path), str(audio_path))

        # 2. Transcribe with WhisperX (gives perfect word-level timestamps)
        transcription = transcription_service.transcribe_audio(str(audio_path))
        # transcription now has: segments = [{"id":.., "start": 1.23, "end": 4.56, "text": "..."}, ...]
        print(transcription)
        # 3. Translate each segment individually
        translated_segments = []
        for seg in transcription["text"]:
            translated = await translation_service.translate_text(seg["text"], target_lang=target_language)
            translated_segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "duration": seg["end"] - seg["start"],
                "translated_text": translated
            })

        # 4. Generate + speed-adjust TTS segment by segment
        final_audio_path = temp_dir / "final_dubbed_audio.wav"
        await tts_service.generate_perfectly_synced_audio(
            segments=translated_segments,
            output_path=str(final_audio_path),
            voice=tts_service.get_voice_for_language(target_language),  # e.g. "ru-RU-SvetlanaNeural"
        )

        # 5. Replace audio with perfect length match
        output_video_path = output_dir / f"dubbed_{file.filename}"
        video_service.replace_audio_perfect_sync(
            video_path=str(video_path),
            audio_path=str(final_audio_path),
            output_path=str(output_video_path)
        )

        return {
            "status": "success",
            "translated_video": str(output_video_path),
            "original_language": transcription.get("language", "unknown"),
            "target_language": target_language,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Optional: clean temp files
        pass