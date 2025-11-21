import asyncio
import edge_tts
from pathlib import Path

# Your target languages
TARGET_LANGUAGES = {
    "ru": "ru-RU",
    "en": "en-US",
    "es": "es-ES",
    "fr": "fr-FR",
    "de": "de-DE",
    "hy": "hy-AM"
}

# Sample text for each language
SAMPLE_TEXTS = {
    "ru": "Привет, это пример голоса.",
    "en": "Hello, this is a voice sample.",
    "es": "Hola, este es un ejemplo de voz.",
    "fr": "Bonjour, ceci est un exemple de voix.",
    "de": "Hallo, dies ist ein Stimmbeispiel.",
    "hy": "Բարև, սա ձայնի օրինակ է."
}

MAX_VOICES_PER_LANGUAGE = 6


async def generate_voice_sample(voice_name: str, text: str, output_path: str, format: str = "mp3"):
    """
    Generate a voice sample and save it to the specified path
    """
    print(f"Generating sample for {voice_name}...")

    try:
        communicate = edge_tts.Communicate(text, voice_name)
        await communicate.save(output_path)
        print(f"✓ Saved: {output_path}")
        return True
    except Exception as e:
        print(f"✗ Error generating {voice_name}: {e}")
        return False


async def generate_all_samples(base_dir: str = "../samples", formats: list = ["mp3"], max_voices: int = 6):
    """
    Generate samples for all target languages and voices

    Args:
        base_dir: Base directory for samples (default: "../samples")
        formats: List of formats to generate (default: ["mp3"])
        max_voices: Maximum number of voices per language (default: 6)
    """
    # Create base directory
    base_path = Path(base_dir)
    base_path.mkdir(exist_ok=True)
    print(f"Base directory: {base_path.absolute()}\n")

    # Get all available voices
    print("Fetching available voices...")
    all_voices = await edge_tts.list_voices()
    print(f"Found {len(all_voices)} total voices\n")

    stats = {
        "total": 0,
        "success": 0,
        "failed": 0
    }

    # Process each target language
    for lang_code, locale_prefix in TARGET_LANGUAGES.items():
        print(f"\n{'=' * 60}")
        print(f"Processing language: {lang_code} ({locale_prefix})")
        print(f"{'=' * 60}")

        # Find matching voices
        matching_voices = [
            v for v in all_voices
            if v['Locale'].startswith(locale_prefix)
        ]

        # Limit to max_voices
        total_found = len(matching_voices)
        matching_voices = matching_voices[:max_voices]

        print(f"Found {total_found} voices for {lang_code}, using {len(matching_voices)}\n")

        # Get sample text for this language
        sample_text = SAMPLE_TEXTS.get(lang_code, "Hello, this is a sample.")

        # Generate samples for each voice
        for voice in matching_voices:
            voice_name = voice['ShortName']
            gender = voice['Gender']

            # Create directory structure: samples/[locale]/[voice_name]/
            voice_dir = base_path / lang_code / voice_name
            voice_dir.mkdir(parents=True, exist_ok=True)

            # Generate for each format
            for fmt in formats:
                if fmt == "mp3":
                    output_file = voice_dir / "sample.mp3"
                    stats["total"] += 1
                    success = await generate_voice_sample(voice_name, sample_text, str(output_file))
                    if success:
                        stats["success"] += 1
                    else:
                        stats["failed"] += 1
                elif fmt == "wav":
                    # For WAV, we need to convert from MP3
                    # This requires ffmpeg to be installed
                    mp3_file = voice_dir / "sample_temp.mp3"
                    wav_file = voice_dir / "sample.wav"

                    stats["total"] += 1
                    success = await generate_voice_sample(voice_name, sample_text, str(mp3_file))

                    if success:
                        # Convert to WAV using ffmpeg
                        try:
                            import subprocess
                            subprocess.run([
                                'ffmpeg', '-i', str(mp3_file),
                                '-acodec', 'pcm_s16le',
                                '-ar', '44100',
                                str(wav_file),
                                '-y'
                            ], check=True, capture_output=True)

                            # Remove temp MP3 file
                            mp3_file.unlink()
                            print(f"✓ Converted to WAV: {wav_file}")
                            stats["success"] += 1
                        except Exception as e:
                            print(f"✗ Error converting to WAV: {e}")
                            stats["failed"] += 1
                    else:
                        stats["failed"] += 1

    # Print summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total samples attempted: {stats['total']}")
    print(f"Successfully generated: {stats['success']}")
    print(f"Failed: {stats['failed']}")
    print(f"\nSamples saved in: {base_path.absolute()}/")


async def generate_samples_for_language(lang_code: str, base_dir: str = "../samples", formats: list = ["mp3"],
                                        max_voices: int = 6):
    """
    Generate samples for a specific language only
    """
    if lang_code not in TARGET_LANGUAGES:
        print(f"Error: Language '{lang_code}' not in target languages")
        return

    locale_prefix = TARGET_LANGUAGES[lang_code]
    all_voices = await edge_tts.list_voices()

    matching_voices = [
        v for v in all_voices
        if v['Locale'].startswith(locale_prefix)
    ]

    # Limit to max_voices
    matching_voices = matching_voices[:max_voices]

    print(f"Generating samples for {len(matching_voices)} {lang_code} voices...")

    sample_text = SAMPLE_TEXTS.get(lang_code, "Hello, this is a sample.")

    for voice in matching_voices:
        voice_name = voice['ShortName']
        voice_dir = Path(base_dir) / lang_code / voice_name
        voice_dir.mkdir(parents=True, exist_ok=True)

        for fmt in formats:
            if fmt == "mp3":
                output_file = voice_dir / "sample.mp3"
                await generate_voice_sample(voice_name, sample_text, str(output_file))


# Main execution
if __name__ == "__main__":
    print("Voice Sample Generator")
    print("=" * 60)

    # Option 1: Generate all samples (MP3 only) - max 6 voices per language
    asyncio.run(generate_all_samples(base_dir="../samples", formats=["mp3"], max_voices=MAX_VOICES_PER_LANGUAGE))

    # Option 2: Generate all samples (MP3 and WAV - requires ffmpeg)
    # asyncio.run(generate_all_samples(base_dir="../samples", formats=["mp3", "wav"], max_voices=6))

    # Option 3: Generate samples for specific language only
    # asyncio.run(generate_samples_for_language("ru", base_dir="../samples", formats=["mp3"], max_voices=6))