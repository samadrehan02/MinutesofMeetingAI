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
from fastapi.concurrency import run_in_threadpool
from app.schemas import MinutesOfMeeting

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

def shadow_validate_minutes(minutes: dict):
    try:
        MinutesOfMeeting.parse_obj(minutes)
    except Exception as e:
        print("⚠️ Minutes schema validation failed:")
        print(e)

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


def process_chunks(transcript: str):
    chunks = chunk_text(transcript)

    topics = []
    decisions = []
    tasks = []

    seen_topics = set()
    seen_decisions = set()
    seen_tasks = set()  # (description, owner, deadline)

    for chunk in chunks:
        chunk_raw = extract_chunk_facts(chunk)
        chunk_data = json.loads(chunk_raw or "{}")

        # Topics (preserve order)
        for t in chunk_data.get("topics", []):
            if isinstance(t, str):
                t = t.strip()
                if t and t not in seen_topics:
                    seen_topics.add(t)
                    topics.append(t)

        # Decisions (preserve order)
        for d in chunk_data.get("decisions", []):
            if isinstance(d, str):
                d = d.strip()
                if d and d not in seen_decisions:
                    seen_decisions.add(d)
                    decisions.append(d)

        # Tasks (dedupe exact matches only)
        for task in chunk_data.get("tasks", []):
            if not isinstance(task, dict):
                continue

            desc = task.get("description")
            if not isinstance(desc, str):
                continue

            desc = desc.strip()
            if not desc:
                continue

            owner = task.get("owner") or "Unassigned"
            deadline = task.get("deadline") or "N/A"

            key = (desc, owner, deadline)
            if key in seen_tasks:
                continue

            seen_tasks.add(key)
            tasks.append({
                "description": desc,
                "owner": owner,
                "deadline": deadline,
            })

    minutes_raw = synthesize_minutes(
        topics=topics,
        decisions=decisions,
        tasks=tasks,
    )

    return json.loads(minutes_raw)


@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

@app.post("/minutes")
async def generate_minutes(file: UploadFile = File(...)):
    print(">>> /minutes endpoint hit")
    print(">>> filename:", file.filename)

    uploaded_path = None
    derived_audio_path = None

    try:
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

        # STREAM upload to disk (NO RAM SPIKE)
        suffix = Path(file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            uploaded_path = tmp.name

        input_audio_path = uploaded_path

        # If video → extract audio, then DELETE video immediately
        if filename.endswith(VIDEO_EXTENSIONS):
            print(">>> extracting audio from video")
            derived_audio_path = await run_in_threadpool(
                extract_audio_from_video,
                uploaded_path
            )
            input_audio_path = derived_audio_path

            os.remove(uploaded_path)
            uploaded_path = None  # prevent double-delete

        print(">>> starting transcription")
        transcript = await run_in_threadpool(
            transcribe,
            input_audio_path
        )
        print(">>> transcription done")

        # Free GPU + Python memory ASAP
        release_gpu()
        gc.collect()

        print(">>> extracting minutes")

        # SHORT MEETINGS → single Ollama call
        if len(transcript) <= MAX_TRANSCRIPT_CHARS:
            minutes_raw = await run_in_threadpool(
                extract_minutes,
                transcript
            )
            minutes = (
                json.loads(minutes_raw)
                if isinstance(minutes_raw, str)
                else minutes_raw
            )
        else:
            # LONG MEETINGS → chunking
            print(">>> transcript too long, using chunking")
            minutes = await run_in_threadpool(
                process_chunks,
                transcript
            )

        shadow_validate_minutes(minutes)

        return {
            "transcript": transcript,
            "minutes_of_meeting": minutes,
        }

    except HTTPException:
        # Explicit, expected errors → pass through
        raise

    except Exception as e:
        # Unexpected errors → clean API response
        print("❌ Unhandled error in /minutes:", e)
        raise HTTPException(
            status_code=500,
            detail="Internal processing error. Please try again."
        )

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
