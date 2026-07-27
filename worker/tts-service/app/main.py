# import shutil
# import tempfile
# from pathlib import Path
import shutil
import tempfile
import traceback
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

app = FastAPI(title="PersonalVoice Reader — TTS service", version="0.1.0")

_model = None  # lazy singleton; loading is slow and needs network access on first run

# A real model.pth is well over a gigabyte. Anything drastically smaller
# means the download silently failed (e.g. a network/proxy block that
# returned an error page instead of raising) — ModelManager doesn't
# validate this itself, so we do, rather than let a corrupted "model"
# fail confusingly several calls later.
MIN_EXPECTED_MODEL_BYTES = 500_000_000


def _get_model():
    global _model
    if _model is None:
        import torch
        from TTS.tts.configs.xtts_config import XttsConfig
        from TTS.tts.models.xtts import Xtts
        from TTS.utils.manage import ModelManager

        model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
        manager = ModelManager()
        model_path, _, _ = manager.download_model(model_name)

        config_path = Path(model_path) / "config.json"

        if not config_path.exists():
            raise RuntimeError(f"config.json not found in {model_path}")

        print(f"model_path  = {model_path}")
        print(f"config_path = {config_path}")
        # model_path, config_path, _ = manager.download_model(model_name)

        # checkpoint_file = Path(model_path) / "model.pth"
        # if not checkpoint_file.exists() or checkpoint_file.stat().st_size < MIN_EXPECTED_MODEL_BYTES:
        #     actual_size = checkpoint_file.stat().st_size if checkpoint_file.exists() else 0
        #     preview = ""
        #     try:
        #         preview = checkpoint_file.read_text(errors="replace")[:200]
        #     except Exception:
        #         pass
        #     raise RuntimeError(
        #         f"XTTS model download looks corrupted or incomplete: {checkpoint_file} is only "
        #         f"{actual_size} bytes (expected 1GB+). This usually means the download was "
        #         f"blocked or interrupted rather than a code error — check network/proxy access "
        #         f"to huggingface.co and coqui.gateway.scarf.sh, and check disk space. "
        #         + (f"File contents: {preview!r}" if preview else "")
        #     )

        #     config = XttsConfig()
        #     config.load_json(config_path)
        #     model = Xtts.init_from_config(config)
        #     model.load_checkpoint(config, checkpoint_dir=model_path, eval=True)
        #     if torch.cuda.is_available():
        #         model.cuda()
        #     _model = model
        # return _model

        config = XttsConfig()

        # Newer versions of Coqui return None for config_path.
        # if config_path is None:
        #     config_path = Path(model_path) / "config.json"

        # if not Path(config_path).exists():
        #     raise FileNotFoundError(
        #         f"config.json not found at {config_path}"
        #     )

        print(f"Loading XTTS from {model_path}")
        print(f"Using config {config_path}")

        config.load_json(str(config_path))

        model = Xtts.init_from_config(config)

        print("Loading checkpoint...")
        model.load_checkpoint(
            config,
            checkpoint_dir=str(model_path),
            eval=True,
        )

        print("Checkpoint loaded.")

        if torch.cuda.is_available():
            model.cuda()

        print("XTTS ready.")

        _model = model

    return _model

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": _model is not None}


@app.post("/clone")
async def clone(file: UploadFile):
    """
    Accepts a reference recording, computes XTTS v2 conditioning latents,
    and returns them as a downloadable .pt file. Stateless: the caller
    (the main backend) is responsible for persisting the result.
    """
    import torch

    with tempfile.TemporaryDirectory() as tmp:
        source_path = Path(tmp) / (file.filename or "source.wav")
        with source_path.open("wb") as out:
            shutil.copyfileobj(file.file, out)

        try:
            model = _get_model()
            gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(
                audio_path=[str(source_path)]
            )
        # except Exception as exc:
        #     raise HTTPException(status_code=500, detail=f"Cloning failed: {exc}") from exc
        except Exception as exc:
            print("\n===== CLONE ERROR =====")
            traceback.print_exc()
            print("=======================\n")

            raise HTTPException(
                status_code=500,
                detail=f"Cloning failed: {exc}",
            ) from exc
        artifact_path = Path(tmp) / "voice_profile.pt"
        torch.save(
            {"gpt_cond_latent": gpt_cond_latent, "speaker_embedding": speaker_embedding},
            artifact_path,
        )
        # FileResponse streams before the tempdir is cleaned up on most
        # ASGI servers, but to be safe, copy outside the context first.
        persistent_path = Path(tempfile.mkstemp(suffix=".pt")[1])
        shutil.copy(artifact_path, persistent_path)

    return FileResponse(persistent_path, media_type="application/octet-stream", filename="voice_profile.pt")


@app.post("/synthesize")
async def synthesize(text: str = Form(...), profile: UploadFile = None):
    """
    Renders `text` as speech conditioned on a previously-cloned voice
    profile (the .pt file /clone returned). Returns a WAV file. Stateless
    — the caller chunks chapter text into segments and concatenates the
    resulting WAV files itself.
    """
    import torch
    import torchaudio

    with tempfile.TemporaryDirectory() as tmp:
        profile_path = Path(tmp) / "voice_profile.pt"
        with profile_path.open("wb") as out:
            shutil.copyfileobj(profile.file, out)

        try:
            model = _get_model()
            loaded = torch.load(profile_path)
            out_data = model.inference(
                text,
                language="en",
                gpt_cond_latent=loaded["gpt_cond_latent"],
                speaker_embedding=loaded["speaker_embedding"],
            )
        # except Exception as exc:
            # raise HTTPException(status_code=500, detail=f"Synthesis failed: {exc}") from exc
        except Exception as exc:
            print("\n===== SYNTHESIS ERROR =====")
            traceback.print_exc()
            print("===========================\n")

            raise HTTPException(
                status_code=500,
                detail=f"Synthesis failed: {exc}",
            ) from exc
        wav_path = Path(tmp) / "segment.wav"
        wav_tensor = torch.tensor(out_data["wav"]).unsqueeze(0)
        torchaudio.save(str(wav_path), wav_tensor, sample_rate=24000)

        persistent_path = Path(tempfile.mkstemp(suffix=".wav")[1])
        shutil.copy(wav_path, persistent_path)

    return FileResponse(persistent_path, media_type="audio/wav", filename="segment.wav")
