import json
import wave
from pathlib import Path

from app.tts.base import CloningResult, VoiceCloningEngine

WORDS_PER_MINUTE = 150  # rough speaking rate, used to fake a plausible duration


class DummyEngine(VoiceCloningEngine):
    """
    Not real voice cloning or synthesis. Reads basic properties of the
    reference audio and writes them as a stand-in "profile", and turns
    text into silence sized to roughly match how long it'd take to speak
    — so the rest of the pipeline (status transitions, storage, playback
    UI, caching) can be built and tested without the multi-gigabyte
    TTS/torch install. Selected via TTS_ENGINE=dummy.
    """

    name = "dummy"

    def clone(self, source_audio_path: Path, output_dir: Path) -> CloningResult:
        profile = {"source_file": source_audio_path.name}
        if source_audio_path.suffix.lower() == ".wav":
            with wave.open(str(source_audio_path), "rb") as f:
                profile["frames"] = f.getnframes()
                profile["sample_rate"] = f.getframerate()

        output_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = output_dir / "voice_profile.json"
        artifact_path.write_text(json.dumps(profile))

        return CloningResult(artifact_path=str(artifact_path), engine=self.name)

    def synthesize(self, text: str, voice_profile_path: Path, output_wav_path: Path) -> None:
        word_count = max(1, len(text.split()))
        seconds = max(0.5, (word_count / WORDS_PER_MINUTE) * 60)
        sample_rate = 16000
        n_frames = int(seconds * sample_rate)

        output_wav_path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(output_wav_path), "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            f.writeframes(b"\x00\x00" * n_frames)
