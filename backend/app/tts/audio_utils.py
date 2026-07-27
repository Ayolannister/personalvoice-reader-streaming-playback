import subprocess
import wave
from pathlib import Path


def concat_wavs_to_mp3(wav_paths: list[Path], output_mp3_path: Path) -> float:
    """
    Concatenates WAV segments in order and encodes the result as MP3.
    Returns the resulting duration in seconds. Requires ffmpeg on PATH.
    """
    if not wav_paths:
        raise ValueError("No audio segments to concatenate")

    output_mp3_path.parent.mkdir(parents=True, exist_ok=True)
    concat_list_path = output_mp3_path.with_suffix(".concat.txt")
    concat_list_path.write_text(
        "\n".join(f"file '{p.resolve()}'" for p in wav_paths), encoding="utf-8"
    )

    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_list_path),
                "-codec:a", "libmp3lame", "-qscale:a", "4",
                str(output_mp3_path),
            ],
            check=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("ffmpeg is not installed or not on PATH") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"ffmpeg failed: {exc.stderr.decode(errors='replace')[-500:]}") from exc
    finally:
        concat_list_path.unlink(missing_ok=True)

    return _wav_total_duration(wav_paths)


def _wav_total_duration(wav_paths: list[Path]) -> float:
    total = 0.0
    for p in wav_paths:
        with wave.open(str(p), "rb") as f:
            total += f.getnframes() / f.getframerate()
    return total
