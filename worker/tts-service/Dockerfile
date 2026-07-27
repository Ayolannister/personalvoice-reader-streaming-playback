# XTTS service isolated in Python 3.11
FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV COQUI_TOS_AGREED=1

# Install ffmpeg with retries
RUN apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip setuptools wheel

# CPU-only build: the default PyPI torch wheel bundles several GB of
# NVIDIA CUDA libraries that are pure dead weight without a GPU, and are
# the most likely cause of "no space left on device" during this build.
# Installed first so requirements.txt's matching pins are already
# satisfied and won't trigger a second, GPU-bundled install.
RUN pip install torch==2.4.1 torchaudio==2.4.1 --index-url https://download.pytorch.org/whl/cpu

RUN pip install -r requirements.txt

COPY app ./app

# Persist downloaded XTTS models
VOLUME ["/root/.local/share/tts"]

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]