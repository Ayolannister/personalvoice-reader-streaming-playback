from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CloningResult:
    artifact_path: str
    engine: str


class VoiceCloningEngine(ABC):
    """
    A voice-cloning engine turns a reference recording into a reusable
    "voice profile" artifact that the audio-generation step conditions
    on when synthesizing chapter audio.

    XTTS v2 cloning is zero-shot: there's no fine-tuning loop, "training"
    means computing conditioning latents from the reference audio once,
    then reusing them for every chapter. That's why this returns a single
    artifact path rather than a long-running job handle.
    """

    name: str

    @abstractmethod
    def clone(self, source_audio_path: Path, output_dir: Path) -> CloningResult:
        """Compute and persist a voice profile from a reference recording."""
        raise NotImplementedError

    @abstractmethod
    def synthesize(self, text: str, voice_profile_path: Path, output_wav_path: Path) -> None:
        """
        Render `text` as speech conditioned on a previously-cloned voice
        profile, writing a WAV file to `output_wav_path`. Called once per
        text segment — the caller is responsible for chunking a chapter's
        text into segments short enough for the model and concatenating
        the resulting WAV files into the final chapter audio.
        """
        raise NotImplementedError
