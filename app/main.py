from dotenv import load_dotenv
load_dotenv()

import json
import os
import tempfile

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.whisper_gpu import transcribe, release_gpu
from app.ollama_client import extract_minutes


app = FastAPI(title="Minutes of Meeting AI")

# Mount static folder
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def read_index():
    return FileResponse("static/index.html")


@app.post("/minutes")
async def generate_minutes(file: UploadFile = File(...)):
    print(">>> /minutes endpoint hit")
    print(">>> filename:", file.filename)

    # Validate file type
    if not file.filename.lower().endswith((".wav", ".mp3", ".m4a", ".webm")):
        raise HTTPException(status_code=400, detail="Unsupported audio format")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(await file.read())
        audio_path = tmp.name

    try:
        print(">>> starting transcription")
        transcript = transcribe(audio_path)
        print(">>> transcription done")

        # Free GPU before LLM
        release_gpu()

        print(">>> extracting minutes")
        minutes_raw = extract_minutes(transcript)

        # Ollama returns JSON as string → must parse
        if isinstance(minutes_raw, str):
            minutes = json.loads(minutes_raw)
        else:
            minutes = minutes_raw

        return {
            "transcript": transcript,
            "minutes_of_meeting": minutes
        }

    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)
