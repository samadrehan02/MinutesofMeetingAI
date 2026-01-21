from dotenv import load_dotenv
load_dotenv()

import json
import os
import tempfile

import ffmpeg
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.whisper_gpu import transcribe, release_gpu
from app.ollama_client import extract_minutes


app = FastAPI(title="Minutes of Meeting AI")

# Mount static folder
app.mount("/static", StaticFiles(directory="static"), name="static")


AUDIO_EXTENSIONS = (".wav", ".mp3", ".m4a")
VIDEO_EXTENSIONS = (".mp4", ".webm", ".mkv")


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
            ar="16000"
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

    filename = file.filename.lower()

    if not filename.endswith(AUDIO_EXTENSIONS + VIDEO_EXTENSIONS):
        raise HTTPException(status_code=400, detail="Unsupported file format")

    # Save uploaded file to temp
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(await file.read())
        uploaded_path = tmp.name

    derived_audio_path = None

    try:
        input_audio_path = uploaded_path

        # If video, extract audio
        if filename.endswith(VIDEO_EXTENSIONS):
            print(">>> extracting audio from video")
            derived_audio_path = extract_audio_from_video(uploaded_path)
            input_audio_path = derived_audio_path

        print(">>> starting transcription")
        transcript = transcribe(input_audio_path)
        print(">>> transcription done")

        # Free GPU memory before LLM
        release_gpu()

        print(">>> extracting minutes (single Ollama call)")
        minutes_raw = extract_minutes(transcript)

        # Ollama returns JSON as string → parse
        if isinstance(minutes_raw, str):
            minutes = json.loads(minutes_raw)
        else:
            minutes = minutes_raw

        return {
            "transcript": transcript,
            "minutes_of_meeting": minutes
        }

    finally:
        # Cleanup uploaded file
        if os.path.exists(uploaded_path):
            os.remove(uploaded_path)

        # Cleanup extracted audio if it exists
        if derived_audio_path and os.path.exists(derived_audio_path):
            os.remove(derived_audio_path)
