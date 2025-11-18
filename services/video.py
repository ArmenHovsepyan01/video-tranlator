import os
import ffmpeg
from pathlib import Path

class VideoService:
    def __init__(self, temp_dir: str = "./temp"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)

    def extract_audio_from_video(self, video_path: str, output_audio_path: str) -> str:
        """
        Extract audio from video using FFmpeg
        WhisperX needs audio file, not video!
        """
        try:
            # Extract audio as WAV (best for WhisperX)
            (
                ffmpeg
                .input(video_path)
                .output(output_audio_path, acodec='pcm_s16le', ac=1, ar='16k')
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            return output_audio_path
        except ffmpeg.Error as e:
            raise Exception(f"FFmpeg error: {e.stderr.decode()}")

    def get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds"""
        probe = ffmpeg.probe(video_path)
        duration = float(probe['streams'][0]['duration'])
        return duration

    def replace_audio_in_video(
            self,
            video_path: str,
            new_audio_path: str,
            output_path: str
    ) -> str:
        """
        Replace video's audio track with new audio
        Sync new audio with video
        """
        try:
            video = ffmpeg.input(video_path)
            audio = ffmpeg.input(new_audio_path)

            (
                ffmpeg
                .output(
                    video.video,
                    audio.audio,
                    output_path,
                    vcodec='copy',  # Copy video without re-encoding
                    acodec='aac',  # Encode audio as AAC
                    strict='experimental'
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            return output_path
        except ffmpeg.Error as e:
            raise Exception(f"FFmpeg error: {e.stderr.decode()}")

    def replace_audio_perfect_sync(self, video_path: str, audio_path: str, output_path: str):
        video = ffmpeg.input(video_path)
        audio = ffmpeg.input(audio_path)

        ffmpeg.output(
            video.video, audio.audio,
            output_path,
            vcodec="copy",  # no re-encode video
            acodec="aac",
            shortest=None  # don't cut anything, audio is already exact length
        ).overwrite_output().run(quiet=True)