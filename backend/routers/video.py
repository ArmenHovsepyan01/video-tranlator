from fastapi import APIRouter, HTTPException, File, status, UploadFile
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse
from pathlib import Path
import shutil
import json
from services import VideoService, TranslationService, TranscriptionService, TTSService
import edge_tts
from fastapi.responses import JSONResponse
from itertools import islice

from sympy.codegen.ast import Raise

router = APIRouter(prefix="/video", tags=["Video"])

translation_service = TranslationService()
video_service = VideoService()
transcription_service = TranscriptionService()
tts_service = TTSService()

def send_sse_event(event_type: str, data: dict):
    """Helper to format SSE events"""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

async def process_video_with_progress(file: UploadFile, target_language: str, voice: str):
    print(f"Processing {target_language} {voice}")
    """Process video and yield SSE progress events"""
    upload_dir = Path("./uploads")
    temp_dir = Path("./temp")
    output_dir = Path("./outputs")

    for d in [upload_dir, temp_dir, output_dir]:
        d.mkdir(exist_ok=True)

    video_path = upload_dir / file.filename
    with open(video_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        duration = video_service.get_video_duration(str(video_path))

        if duration > 60:
            raise Exception("Video duration is longer than 1 minute")

        # Progress: Upload complete
        yield send_sse_event("progress", {"stage": "upload", "message": "Video uploaded successfully", "progress": 10})

        # 1. Extract clean WAV audio (16kHz is best for Whisper)
        yield send_sse_event("progress", {"stage": "extract_audio", "message": "Extracting audio from video...", "progress": 20})
        audio_path = temp_dir / "original_audio.wav"
        video_service.extract_audio_from_video(str(video_path), str(audio_path))
        yield send_sse_event("progress", {"stage": "extract_audio", "message": "Audio extracted successfully", "progress": 30})

        # 2. Transcribe with WhisperX (gives perfect word-level timestamps)
        yield send_sse_event("progress", {"stage": "transcribe", "message": "Transcribing audio...", "progress": 40})
        transcription = transcription_service.transcribe_audio(str(audio_path))
        yield send_sse_event("progress", {"stage": "transcribe", "message": f"Transcription complete. Found {len(transcription['text'])} segments.", "progress": 50})

        # 3. Translate each segment individually
        yield send_sse_event("progress", {"stage": "translate", "message": "Translating segments...", "progress": 55})
        translated_segments = []

        if transcription.get("language") != target_language:
            total_segments = len(transcription["text"])
            for idx, seg in enumerate(transcription["text"]):
                translated = await translation_service.translate_text(seg["text"], target_lang=target_language)
                translated_segments.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "duration": seg["end"] - seg["start"],
                    "translated_text": translated
                })
                # Update progress for translation
                translation_progress = 55 + int((idx + 1) / total_segments * 20)
                yield send_sse_event("progress", {
                    "stage": "translate",
                    "message": f"Translated {idx + 1}/{total_segments} segments",
                    "progress": translation_progress
                })
        else:
            raise Exception("Same language")

        # 4. Generate + speed-adjust TTS segment by segment
        yield send_sse_event("progress", {"stage": "tts", "message": "Generating speech...", "progress": 75})
        final_audio_path = temp_dir / "final_dubbed_audio.wav"
        await tts_service.generate_perfectly_synced_audio(
            segments=translated_segments,
            output_path=str(final_audio_path),
            voice=str(voice),
        )
        yield send_sse_event("progress", {"stage": "tts", "message": "Speech generation complete", "progress": 85})

        # 5. Replace audio with perfect length match
        yield send_sse_event("progress", {"stage": "merge", "message": "Merging audio with video...", "progress": 90})
        output_video_path = output_dir / f"dubbed_{file.filename}"
        video_service.replace_audio_perfect_sync(
            video_path=str(video_path),
            audio_path=str(final_audio_path),
            output_path=str(output_video_path)
        )
        yield send_sse_event("progress", {"stage": "merge", "message": "Video processing complete", "progress": 95})

        # Final success event
        yield send_sse_event("complete", {
            "status": "success",
            "translated_video": str(output_video_path).replace("outputs", ""),
            "original_language": transcription.get("language", "unknown"),
            "target_language": target_language,
            "progress": 100
        })

    except Exception as e:
        yield send_sse_event("error", {"message": str(e), "progress": 0})
    finally:
        # Optional: clean temp files
        pass

@router.post("/upload", status_code=status.HTTP_200_OK)
async def upload_video(file: UploadFile = File(...), target_language: str = "ru"):
    """Original endpoint for backward compatibility"""
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

@router.post("/upload-stream")
async def upload_video_stream(file: UploadFile = File(...), target_language: str = "ru", voice: str = "en-US-AdamMultilingualNeural"):
    """Upload video with SSE progress streaming"""
    print("target language: ", target_language, voice)
    return StreamingResponse(
        process_video_with_progress(file, target_language, voice),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/download/{file_path}")
async def download_dubbed_video(file_path: str):
    """Direct download with proper filename"""
    final_audio_path = Path(f"./outputs/{file_path}")

    if not Path(final_audio_path).exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=final_audio_path,
        media_type="video/mp4",
        filename=Path(final_audio_path).name,
        headers={"Content-Disposition": f"attachment; filename={Path(final_audio_path).name}"}
    )

# Your target languages
TARGET_LANGUAGES = {
    "ru": "ru-RU",
    "en": "en-US",
    "es": "es-ES",
    "fr": "fr-FR",
    "de": "de-DE",
    "hy": "hy-AM"
}

@router.get("/voices")
async def get_voices():
    """
    Get available voices for specific languages
    """
    # Get all available voices from edge-tts
    all_voices = await edge_tts.list_voices()

    # Filter and organize voices by target languages
    result = []

    for lang_code, locale_prefix in TARGET_LANGUAGES.items():
        matching_voices = [
            v for v in all_voices
            if v['Locale'].startswith(locale_prefix)
        ]

        if matching_voices:
            voices_list = [
                {
                    "gender": voice['Gender'],
                    "voice": voice['ShortName']
                }
                for voice in islice(matching_voices, 6)
            ]

            result.append({
                "locale": lang_code,
                "voices": voices_list
            })

    return JSONResponse(content=result)


@router.get("/voices/{language}")
async def get_voices_by_language(language: str):
    """
    Get available voices for a specific language
    Example: /voices/en or /voices/hy
    """
    if language not in TARGET_LANGUAGES:
        return JSONResponse(
            content={"error": f"Language '{language}' not supported"},
            status_code=400
        )

    locale_prefix = TARGET_LANGUAGES[language]
    all_voices = await edge_tts.list_voices()

    matching_voices = [
        {
            "gender": voice['Gender'],
            "voice": voice['ShortName']
        }
        for voice in all_voices
        if voice['Locale'].startswith(locale_prefix)
    ]

    return JSONResponse(content={
        "locale": language,
        "voices": matching_voices
    })