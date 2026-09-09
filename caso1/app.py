from __future__ import annotations

import os
import shutil
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp
from flask import Flask, jsonify, render_template, request, send_file


BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_ROOT = Path(os.getenv("DOWNLOAD_DIR", BASE_DIR / "downloads")).resolve()
DOWNLOAD_ROOT.mkdir(parents=True, exist_ok=True)

ALLOWED_HOSTS = (
    "youtube.com",
    "youtu.be",
    "instagram.com",
    "tiktok.com",
    "facebook.com",
    "fb.watch",
    "linkedin.com",
)
QUALITY_OPTIONS = {
    "best": "bv*+ba/b",
    "1080": "bv*[height<=1080]+ba/b[height<=1080]",
    "720": "bv*[height<=720]+ba/b[height<=720]",
    "480": "bv*[height<=480]+ba/b[height<=480]",
    "audio": "bestaudio/best",
}


def download_format(url: str, quality: str) -> str:
    """Use TikTok's usually pre-combined streams instead of requiring split A/V."""
    host = (urlparse(url).hostname or "").lower().rstrip(".")
    if host == "tiktok.com" or host.endswith(".tiktok.com"):
        if quality == "audio":
            return "bestaudio/best"
        if quality == "best":
            return "best"
        return f"best[height<={quality}]/best"
    return QUALITY_OPTIONS[quality]

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024

jobs: dict[str, dict] = {}
jobs_lock = threading.Lock()
executor = ThreadPoolExecutor(max_workers=int(os.getenv("MAX_WORKERS", "2")))


def is_allowed_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
        host = (parsed.hostname or "").lower().rstrip(".")
        return parsed.scheme in {"http", "https"} and any(
            host == allowed or host.endswith(f".{allowed}") for allowed in ALLOWED_HOSTS
        )
    except ValueError:
        return False


def update_job(job_id: str, **values) -> None:
    with jobs_lock:
        if job_id in jobs:
            jobs[job_id].update(values)


def progress_hook(job_id: str):
    def hook(data: dict) -> None:
        if data.get("status") == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            downloaded = data.get("downloaded_bytes", 0)
            progress = round(downloaded * 100 / total, 1) if total else 0
            update_job(
                job_id,
                status="downloading",
                progress=min(progress, 99),
                speed=data.get("_speed_str", ""),
                eta=data.get("_eta_str", ""),
            )
        elif data.get("status") == "finished":
            update_job(job_id, status="processing", progress=99, eta="")

    return hook


def run_download(job_id: str, url: str, quality: str) -> None:
    job_dir = DOWNLOAD_ROOT / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    audio_only = quality == "audio"
    options = {
        "format": download_format(url, quality),
        "outtmpl": str(job_dir / "%(title).120B [%(id)s].%(ext)s"),
        "noplaylist": True,
        "restrictfilenames": True,
        "windowsfilenames": True,
        "merge_output_format": "mp4",
        "progress_hooks": [progress_hook(job_id)],
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 30,
        "retries": 3,
        "fragment_retries": 3,
        "js_runtimes": {"node": {}},
        "postprocessors": (
            [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]
            if audio_only
            else []
        ),
    }

    try:
        update_job(job_id, status="starting")
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(url, download=True)
            prepared = Path(downloader.prepare_filename(info))

        candidates = [p for p in job_dir.iterdir() if p.is_file() and not p.name.endswith((".part", ".ytdl"))]
        if not candidates:
            raise RuntimeError("La descarga terminó, pero no se generó ningún archivo.")

        preferred_suffix = ".mp3" if audio_only else ".mp4"
        output = next((p for p in candidates if p.suffix.lower() == preferred_suffix), None)
        output = output or max(candidates, key=lambda item: item.stat().st_mtime)
        update_job(
            job_id,
            status="ready",
            progress=100,
            filename=output.name,
            title=info.get("title") or prepared.stem,
            platform=info.get("extractor_key") or info.get("extractor") or "Web",
            size=output.stat().st_size,
            finished_at=time.time(),
        )
    except Exception as exc:
        message = str(exc).replace("ERROR: ", "").strip()
        update_job(
            job_id,
            status="error",
            error=message[:500] or "No fue posible descargar este contenido.",
            finished_at=time.time(),
        )


def cleanup_expired_jobs() -> None:
    ttl = int(os.getenv("DOWNLOAD_TTL_SECONDS", "3600"))
    while True:
        time.sleep(300)
        cutoff = time.time() - ttl
        with jobs_lock:
            expired = [key for key, value in jobs.items() if value.get("finished_at", time.time()) < cutoff]
            for key in expired:
                jobs.pop(key, None)
        for key in expired:
            shutil.rmtree(DOWNLOAD_ROOT / key, ignore_errors=True)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.post("/api/downloads")
def create_download():
    data = request.get_json(silent=True) or {}
    url = str(data.get("url", "")).strip()
    quality = str(data.get("quality", "720")).strip()

    if not is_allowed_url(url):
        return jsonify(error="Ingresa una URL válida de una plataforma compatible."), 400
    if quality not in QUALITY_OPTIONS:
        return jsonify(error="Selecciona una calidad válida."), 400

    job_id = uuid.uuid4().hex
    with jobs_lock:
        jobs[job_id] = {
            "id": job_id,
            "status": "queued",
            "progress": 0,
            "created_at": time.time(),
        }
    executor.submit(run_download, job_id, url, quality)
    return jsonify(id=job_id, status="queued"), 202


@app.get("/api/downloads/<job_id>")
def download_status(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return jsonify(error="Descarga no encontrada o expirada."), 404
        public_job = {key: value for key, value in job.items() if key not in {"created_at", "finished_at"}}
    if public_job.get("status") == "ready":
        public_job["download_url"] = f"/api/downloads/{job_id}/file"
    return jsonify(public_job)


@app.get("/api/downloads/<job_id>/file")
def download_file(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job or job.get("status") != "ready":
            return jsonify(error="El archivo todavía no está disponible."), 404
        filename = job["filename"]

    path = (DOWNLOAD_ROOT / job_id / filename).resolve()
    if path.parent != (DOWNLOAD_ROOT / job_id).resolve() or not path.is_file():
        return jsonify(error="Archivo no encontrado."), 404
    return send_file(path, as_attachment=True, download_name=filename)


threading.Thread(target=cleanup_expired_jobs, daemon=True, name="download-cleaner").start()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
