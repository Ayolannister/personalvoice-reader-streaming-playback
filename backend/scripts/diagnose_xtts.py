"""
Step-by-step diagnostic for real XTTS v2 voice cloning. Run this directly
(not through the API) to see exactly which stage fails, with the actual
underlying error rather than a generic "training failed" status.

    python scripts/diagnose_xtts.py /path/to/your/reference-recording.wav

Requires requirements.txt + requirements-tts.txt installed first.
"""
import sys
import time
from pathlib import Path

MIN_EXPECTED_MODEL_BYTES = 500_000_000


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/diagnose_xtts.py /path/to/reference.wav")
        sys.exit(1)

    source_path = Path(sys.argv[1])
    if not source_path.exists():
        print(f"File not found: {source_path}")
        sys.exit(1)

    print("=== Step 1: import torch + coqui-tts ===")
    t0 = time.time()
    try:
        import torch
        import torchaudio
        from TTS.tts.configs.xtts_config import XttsConfig
        from TTS.tts.models.xtts import Xtts
        from TTS.utils.manage import ModelManager
    except Exception as e:
        print(f"FAILED to import: {type(e).__name__}: {e}")
        print("-> pip install -r requirements.txt -r requirements-tts.txt")
        sys.exit(1)
    print(f"OK ({time.time() - t0:.1f}s). torch={torch.__version__}, cuda_available={torch.cuda.is_available()}")

    print("\n=== Step 2: trim reference audio to 90s mono ===")
    import subprocess
    import tempfile

    trimmed_path = Path(tempfile.mktemp(suffix=".wav"))
    t0 = time.time()
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(source_path), "-t", "90", "-ac", "1", str(trimmed_path)],
            check=True, capture_output=True,
        )
    except FileNotFoundError:
        print("FAILED: ffmpeg not found on PATH. Install it (apt/brew install ffmpeg).")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"FAILED: ffmpeg error: {e.stderr.decode(errors='replace')[-500:]}")
        sys.exit(1)
    print(f"OK ({time.time() - t0:.1f}s). Trimmed file: {trimmed_path} ({trimmed_path.stat().st_size / 1e6:.1f} MB)")

    print("\n=== Step 3: download XTTS v2 model (first run only, ~2GB) ===")
    print("This talks to coqui.gateway.scarf.sh, which redirects to the actual model host.")
    t0 = time.time()
    try:
        manager = ModelManager()
        model_path, config_path, _ = manager.download_model("tts_models/multilingual/multi-dataset/xtts_v2")
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        print("-> Check general internet access, and specifically that coqui.gateway.scarf.sh")
        print("   and huggingface.co aren't blocked by a firewall, proxy, or VPN.")
        sys.exit(1)

    checkpoint_file = Path(model_path) / "model.pth"
    actual_size = checkpoint_file.stat().st_size if checkpoint_file.exists() else 0
    if actual_size < MIN_EXPECTED_MODEL_BYTES:
        preview = ""
        try:
            preview = checkpoint_file.read_text(errors="replace")[:300]
        except Exception:
            pass
        print(f"FAILED: model.pth is only {actual_size} bytes (expected 1GB+) — the download was")
        print("blocked or interrupted without raising an error. This is the exact failure mode")
        print("I hit in my sandbox (network egress blocked coqui.gateway.scarf.sh).")
        if preview:
            print(f"File contents instead of model weights: {preview!r}")
        print(f"\nDelete the corrupted cache and retry after fixing network access:")
        print(f"  rm -rf {model_path}")
        sys.exit(1)
    print(f"OK ({time.time() - t0:.1f}s). model.pth = {actual_size / 1e9:.2f} GB at {model_path}")

     
    print("\nDownloaded model directory contents:")

    for f in sorted(Path(model_path).iterdir()):
        size = (
            f"{f.stat().st_size / 1e6:.1f} MB"
            if f.is_file()
            else "<DIR>"
        )
        print(f"  {f.name:25} {size}")

    print("\n=== Step 4: load model into memory ===")
    t0 = time.time()
    try:
        config = XttsConfig()

        # ------------------------------------------------------------------
        # Older versions of Coqui returned:
        #
        #   (model_path, config_path, metadata)
        #
        # where config_path pointed directly to config.json.
        #
        # Newer releases return:
        #
        #   (model_path, None, metadata)
        #
        # even though config.json is downloaded correctly into the model
        # directory. If config_path is None, build it manually.
        # ------------------------------------------------------------------

        # Original Claude code:
        #
        # config.load_json(config_path)
        #
        # This now fails with:
        #
        # TypeError:
        # expected str, bytes or os.PathLike object, not NoneType
        #
        # because config_path == None.

        if config_path is None:
            config_path = Path(model_path) / "config.json"

        # Helpful diagnostics
        print(f"model_path  = {model_path}")
        print(f"config_path = {config_path}")

        if not Path(config_path).exists():
            raise FileNotFoundError(
                f"config.json not found at {config_path}"
            )

        config.load_json(str(config_path))

        model = Xtts.init_from_config(config)

        # Original Claude code:
        #
        # model.load_checkpoint(config,
        #                      checkpoint_dir=model_path,
        #                      eval=True)
        #
        # Use str(...) to avoid any Path/object compatibility issues across
        # Coqui versions.

        model.load_checkpoint(
            config,
            checkpoint_dir=str(model_path),
            eval=True,
        )

        if torch.cuda.is_available():
            model.cuda()
    except Exception:
     import traceback
    traceback.print_exc()
    sys.exit(1)

    print("\n=== Step 5: compute conditioning latents (the actual 'cloning' step) ===")
    t0 = time.time()
    try:
        gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(audio_path=[str(trimmed_path)])
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        sys.exit(1)
    print(f"OK ({time.time() - t0:.1f}s). Voice profile computed successfully.")

    print("\n=== Step 6: synthesize a short test sentence ===")
    t0 = time.time()
    try:
        out = model.inference(
            "This is a test of the cloned voice.",
            language="en",
            gpt_cond_latent=gpt_cond_latent,
            speaker_embedding=speaker_embedding,
        )
        out_path = Path("xtts_diagnostic_output.wav")
        wav_tensor = torch.tensor(out["wav"]).unsqueeze(0)
        torchaudio.save(str(out_path), wav_tensor, sample_rate=24000)
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        sys.exit(1)
    print(f"OK ({time.time() - t0:.1f}s). Wrote {out_path.resolve()} — play it to hear the cloned voice.")

    print("\nAll steps passed. Real voice cloning works in this environment.")


if __name__ == "__main__":
    main()
