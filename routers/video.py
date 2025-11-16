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
async def upload_video(file: UploadFile = File(...), target_language: str = "Russian"):
    upload_dir = Path("./uploads")
    temp_dir = Path("./temp")
    output_dir = Path("./outputs")

    for dir in [upload_dir, temp_dir, output_dir]:
        dir.mkdir(exist_ok=True)

    video_path = upload_dir / file.filename
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Step 1: Extract audio from video
        audio_path = temp_dir / f"{file.filename}_audio.wav"
        # video_service.extract_audio_from_video(str(video_path), str(audio_path))

        # Step 2: Transcribe audio with WhisperX
        transcription = transcription_service.transcribe_audio(str(audio_path))
        # Save transcription
        transcription_path = output_dir / f"{file.filename}_transcription.json"
        transcription_service.save_transcription(transcription, str(transcription_path))

        # Step 3: Translate transcription
        translated_segments = await translation_service.translate_segments(
            transcription["text"],
            target_language=target_language,
        )

        # Step 4: Generate speech from translated text
        full_translated_text = " ".join([seg["translated_text"] for seg in translated_segments])
        new_audio_path = temp_dir / f"{file.filename}_translated.mp3"
        await tts_service.generate_speech_edge(
            full_translated_text,
            str(new_audio_path),
            target_language,
        )

        # Step 5: Sync new audio with video
        output_video_path = output_dir / f"translated_{file.filename}"
        video_service.replace_audio_in_video(
            str(video_path),
            str(new_audio_path),
            str(output_video_path)
        )

        return {
            "status": "success",
            "message": "Video translated successfully",
            "original_video": str(video_path),
            "translated_video": str(output_video_path),
            "transcription": str(transcription_path),
            "original_language": transcription["language"],
            "target_language": target_language,
            "full_translated_text": full_translated_text,
        }

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))