import whisperx
import torch

class TranscriptionService:
    def __init__(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        self.device = device
        self.compute_type = "float16" if device == "cuda" else "int8"

    def transcribe_audio(self, audio_path: str, language: str = None) -> dict:
        """
        Transcribe audio using WhisperX

        Args:
            audio_path: Path to audio file (NOT video!)
            language: Source language code (e.g., 'en', 'es') or None for auto-detect

        Returns:
            dict with 'text' and 'segments' (timestamps)
        """
        # Load WhisperX model
        model = whisperx.load_model(
            "base",
            self.device,
            compute_type=self.compute_type
        )

        # Transcribe audio
        result = model.transcribe(audio_path)

        # Align timestamps (optional but recommended)
        model_a, metadata = whisperx.load_align_model(
            language_code=result.get('language'),
            device=self.device
        )
        result = whisperx.align(
            result.get("segments"),
            model_a,
            metadata,
            audio_path,
            self.device
        )

        return {
            "text": result.get("segments"),
            "language": result.get("language"),
            "full_text": " ".join([seg["text"] for seg in result["segments"]])
        }

    def save_transcription(self, transcription: dict, output_path: str):
        """Save transcription to file"""
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(transcription, f, ensure_ascii=False, indent=2)