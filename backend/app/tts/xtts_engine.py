from pathlib import Path

import torch

from app.tts.base import CloningResult, VoiceCloningEngine

_model = None  # lazy-loaded singleton; loading is slow and needs network access on first run

# A real model.pth is well over a gigabyte. Anything drastically smaller
# means the download silently failed (e.g. a network/proxy block that
# returned an error page instead of raising) — ModelManager doesn't
# validate this itself, so we do, rather than let a corrupted "model"
# fail confusingly several calls later.
MIN_EXPECTED_MODEL_BYTES = 500_000_000


def _get_model():
    global _model
    if _model is None:
        # Imported lazily so the rest of the backend works without the
        # heavy TTS/torch dependency stack installed.
        from TTS.tts.configs.xtts_config import XttsConfig
        from TTS.tts.models.xtts import Xtts
        from TTS.utils.manage import ModelManager

        model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
        manager = ModelManager()
        model_path, config_path, _ = manager.download_model(model_name)

        checkpoint_file = Path(model_path) / "model.pth"
        if not checkpoint_file.exists() or checkpoint_file.stat().st_size < MIN_EXPECTED_MODEL_BYTES:
            actual_size = checkpoint_file.stat().st_size if checkpoint_file.exists() else 0
            preview = ""
            try:
                preview = checkpoint_file.read_text(errors="replace")[:200]
            except Exception:
                pass
            raise RuntimeError(
                f"XTTS model download looks corrupted or incomplete: {checkpoint_file} is only "
                f"{actual_size} bytes (expected 1GB+). This usually means the download was "
                f"blocked or interrupted rather than a code error — check network/proxy access "
                f"to huggingface.co and coqui.gateway.scarf.sh, and check disk space. "
                + (f"File contents: {preview!r}" if preview else "")
            )

        config = XttsConfig()
        config.load_json(config_path)
        model = Xtts.init_from_config(config)
        model.load_checkpoint(config, checkpoint_dir=model_path, eval=True)
        if torch.cuda.is_available():
            model.cuda()
        _model = model
    return _model


class XTTSEngine(VoiceCloningEngine):
    name = "xtts"

    def clone(self, source_audio_path: Path, output_dir: Path) -> CloningResult:
        model = _get_model()

        gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(
            audio_path=[str(source_audio_path)]
        )

        output_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = output_dir / "voice_profile.pt"
        torch.save(
            {"gpt_cond_latent": gpt_cond_latent, "speaker_embedding": speaker_embedding},
            artifact_path,
        )

        return CloningResult(artifact_path=str(artifact_path), engine=self.name)

    def synthesize(self, text: str, voice_profile_path: Path, output_wav_path: Path) -> None:
        import torchaudio

        model = _get_model()
        profile = torch.load(voice_profile_path)

        out = model.inference(
            text,
            language="en",
            gpt_cond_latent=profile["gpt_cond_latent"],
            speaker_embedding=profile["speaker_embedding"],
        )

        output_wav_path.parent.mkdir(parents=True, exist_ok=True)
        wav_tensor = torch.tensor(out["wav"]).unsqueeze(0)
        torchaudio.save(str(output_wav_path), wav_tensor, sample_rate=24000)
