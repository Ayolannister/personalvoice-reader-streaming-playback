from pathlib import Path

import httpx

from app.config import get_settings
from app.tts.base import CloningResult, VoiceCloningEngine


class XTTSRemoteEngine(VoiceCloningEngine):
    """
    Same cloning behavior as XTTSEngine, but delegates the actual work to
    the dockerized tts-service over HTTP. Kept in its own container so
    the ~5GB torch/transformers/spacy stack doesn't become a dependency
    of the whole backend.
    """

    name = "xtts_remote"

    def clone(self, source_audio_path: Path, output_dir: Path) -> CloningResult:
        settings = get_settings()
        url = f"{settings.tts_service_url.rstrip('/')}/clone"

        with source_audio_path.open("rb") as f:
            files = {"file": (source_audio_path.name, f)}
            try:
                # Cloning can take a while on CPU or on first call (model
                # load + possible download), so allow a generous timeout.
                resp = httpx.post(url, files=files, timeout=settings.tts_clone_timeout_seconds)
            except httpx.TimeoutException as exc:
                raise RuntimeError(
                    f"The TTS service didn't finish cloning within "
                    f"{settings.tts_clone_timeout_seconds}s. It may still be running — "
                    f"this isn't a 'service is down' error, just slower than the timeout. "
                    f"Increase TTS_CLONE_TIMEOUT_SECONDS if this happens consistently. ({exc})"
                ) from exc
            except httpx.RequestError as exc:
                raise RuntimeError(
                    f"Couldn't reach the TTS service at {settings.tts_service_url}. "
                    f"Is it running? ({exc})"
                ) from exc

        if resp.status_code != 200:
            detail = resp.text
            try:
                detail = resp.json().get("detail", detail)
            except Exception:
                pass
            raise RuntimeError(f"TTS service returned an error: {detail}")

        output_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = output_dir / "voice_profile.pt"
        artifact_path.write_bytes(resp.content)

        return CloningResult(artifact_path=str(artifact_path), engine=self.name)

    def synthesize(self, text: str, voice_profile_path: Path, output_wav_path: Path) -> None:
        settings = get_settings()
        url = f"{settings.tts_service_url.rstrip('/')}/synthesize"

        with voice_profile_path.open("rb") as f:
            files = {"profile": (voice_profile_path.name, f)}
            data = {"text": text}
            try:
                # XTTS v2 on CPU is genuinely slow — real-world reports
                # are commonly well under real-time (i.e. synthesizing a
                # few seconds of speech can itself take tens of seconds).
                # A short default timeout here doesn't make it faster, it
                # just turns "slow" into a confusing false-negative error,
                # so this defaults high. httpx.TimeoutException must be
                # checked before the broader RequestError it subclasses.
                resp = httpx.post(url, data=data, files=files, timeout=settings.tts_synthesize_timeout_seconds)
            except httpx.TimeoutException as exc:
                raise RuntimeError(
                    f"The TTS service didn't finish this segment within "
                    f"{settings.tts_synthesize_timeout_seconds}s. It may still be running — "
                    f"this isn't a 'service is down' error, just slower than the timeout. "
                    f"Increase TTS_SYNTHESIZE_TIMEOUT_SECONDS if this happens consistently, "
                    f"or use a GPU if available (CPU inference is the usual cause). ({exc})"
                ) from exc
            except httpx.RequestError as exc:
                raise RuntimeError(
                    f"Couldn't reach the TTS service at {settings.tts_service_url}. "
                    f"Is it running? ({exc})"
                ) from exc

        if resp.status_code != 200:
            detail = resp.text
            try:
                detail = resp.json().get("detail", detail)
            except Exception:
                pass
            raise RuntimeError(f"TTS service returned an error: {detail}")

        output_wav_path.parent.mkdir(parents=True, exist_ok=True)
        output_wav_path.write_bytes(resp.content)
