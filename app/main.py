from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import tempfile
import os
from app.whisper_gpu import transcribe, release_gpu
from app.ollama_client import extract_minutes
from app.chunking import chunk_text
from app.ollama_client import extract_chunk_summary, aggregate_minutes
from app.ollama_client import normalize_partials


app = FastAPI(title="Minutes of Meeting AI")

# Mount static folder
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

@app.post("/minutes")
async def generate_minutes(file: UploadFile = File(...)):
    print(">>>/minutes endpoint hit")
    print(">>> filename:", file.filename)
    # Validate file type
    if not file.filename.lower().endswith((".wav", ".mp3", ".m4a", ".webm")):
        raise HTTPException(status_code=400, detail="Unsupported audio format")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(await file.read())
        audio_path = tmp.name

    try:
        print(">>>starting transcription")
        # Step 1: Transcription (GPU)
        transcript = transcribe(audio_path)
        print(">>>transcription done")
        # Step 2: Clear VRAM for LLM
        release_gpu()

        chunks = chunk_text(transcript)

        partial_results = []

        for chunk in chunks:
            result = extract_chunk_summary(chunk)
            partial_results.append(result)

        # 4. Aggregate
        normalized = normalize_partials(partial_results)
        minutes = aggregate_minutes(partial_results)


        return {
            "transcript": transcript,
            "minutes_of_meeting": minutes
        }
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)