from dotenv import load_dotenv
load_dotenv()

import json
import os
import tempfile
import shutil
import gc
from pathlib import Path

import ffmpeg
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.chunking import chunk_text
from app.ollama_client import (
    extract_chunk_facts,
    synthesize_minutes,
    extract_minutes,
)
from app.whisper_gpu import transcribe, release_gpu


app = FastAPI(title="Minutes of Meeting AI")

# Mount static folder
app.mount("/static", StaticFiles(directory="static"), name="static")


AUDIO_EXTENSIONS = (".wav", ".mp3", ".m4a")
VIDEO_EXTENSIONS = (".mp4", ".webm", ".mkv")

MAX_TRANSCRIPT_CHARS = 12000
MAX_UPLOAD_BYTES = 600 * 1024 * 1024  # 600 MB HARD LIMIT (laptop safe)


def extract_audio_from_video(video_path: str) -> str:
    """
    Extract mono 16kHz MP3 audio from a video file for Whisper.
    """
    audio_path = video_path + ".mp3"

    (
        ffmpeg
        .input(video_path)
        .output(
            audio_path,
            format="mp3",
            acodec="libmp3lame",
            ac=1,
            ar="16000",
        )
        .overwrite_output()
        .run(quiet=True)
    )

    return audio_path


@app.get("/")
async def read_index():
    return FileResponse("static/index.html")


@app.post("/minutes")
async def generate_minutes(file: UploadFile = File(...)):
    print(">>> /minutes endpoint hit")
    print(">>> filename:", file.filename)

    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    filename = file.filename.lower()

    if not filename.endswith(AUDIO_EXTENSIONS + VIDEO_EXTENSIONS):
        raise HTTPException(status_code=400, detail="Unsupported file format")

    # HARD SIZE LIMIT (prevents system death)
    if file.size and file.size > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="File too large. Please upload a shorter recording.",
        )

    uploaded_path = None
    derived_audio_path = None

    try:
        # STREAM upload to disk (NO RAM SPIKE)
        suffix = Path(file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            uploaded_path = tmp.name

        input_audio_path = uploaded_path

        # If video → extract audio, then DELETE video immediately
        if filename.endswith(VIDEO_EXTENSIONS):
            print(">>> extracting audio from video")
            derived_audio_path = extract_audio_from_video(uploaded_path)
            input_audio_path = derived_audio_path

            os.remove(uploaded_path)
            uploaded_path = None  # prevent double-delete

        print(">>> starting transcription")
        transcript = transcribe(input_audio_path)
        print(">>> transcription done")

        # Free GPU + Python memory ASAP
        release_gpu()
        gc.collect()

        print(">>> extracting minutes")

        # SHORT MEETINGS → single Ollama call
        if len(transcript) <= MAX_TRANSCRIPT_CHARS:
            minutes_raw = extract_minutes(transcript)
            minutes = (
                json.loads(minutes_raw)
                if isinstance(minutes_raw, str)
                else minutes_raw
            )

        # LONG MEETINGS → chunking
        else:
            print(">>> transcript too long, using chunking")

            chunks = chunk_text(transcript)

            all_topics = set()
            all_decisions = set()
            all_tasks = []

            for i, chunk in enumerate(chunks):
                print(f">>> extracting facts from chunk {i+1}/{len(chunks)}")
                chunk_raw = extract_chunk_facts(chunk)
                chunk_data = json.loads(chunk_raw or "{}")

                for t in chunk_data.get("topics", []):
                    if isinstance(t, str) and t.strip():
                        all_topics.add(t.strip())

                for d in chunk_data.get("decisions", []):
                    if isinstance(d, str) and d.strip():
                        all_decisions.add(d.strip())

                for task in chunk_data.get("tasks", []):
                    if (
                        isinstance(task, dict)
                        and isinstance(task.get("description"), str)
                        and task["description"].strip()
                    ):
                        all_tasks.append({
                            "description": task["description"].strip(),
                            "owner": task.get("owner") or "Unassigned",
                            "deadline": task.get("deadline") or "N/A",
                        })

            minutes_raw = synthesize_minutes(
                topics=list(all_topics),
                decisions=list(all_decisions),
                tasks=all_tasks,
            )

            minutes = json.loads(minutes_raw)

        return {
            "transcript": transcript,
            "minutes_of_meeting": minutes,
        }

    finally:
        # Cleanup extracted audio
        if derived_audio_path and os.path.exists(derived_audio_path):
            os.remove(derived_audio_path)

        # Cleanup upload if still present
        if uploaded_path and os.path.exists(uploaded_path):
            os.remove(uploaded_path)

        # Ensure file handle closed
        try:
            file.file.close()
        except Exception:
            pass
