# syntax=docker/dockerfile:1.4
# REPLACE_ME: minimal working Dockerfile so nightly.yml/release.yml build out of the box.
# Adjust to your real service's runtime needs (entrypoint, exposed ports, extra deps).
# Note: this builds the app image only. Your HA add-on folder(s) (REPLACE_ME_ADDON_DIR)
# ship their own thin Dockerfile that just does FROM ghcr.io/automationnexus/<image>:<tag>.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --home-dir /app app

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --no-cache-dir .

RUN chown -R app:app /app
USER app

CMD ["python", "-c", "import REPLACE_ME; print(REPLACE_ME.__version__)"]
