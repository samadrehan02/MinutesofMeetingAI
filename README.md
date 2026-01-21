# Minutes of Meeting AI

A local, privacy-preserving Minutes of Meeting (MoM) generator that converts long
audio or video recordings into structured meeting minutes using Whisper (GPU)
and Ollama (local LLM).

This project is designed to handle real-world meetings such as municipal council
sessions and long corporate meetings while remaining safe to run on a developer
laptop.

---

## Features

- Audio and video upload support
- Automatic audio extraction from video files
- GPU-accelerated transcription using Whisper
- Local LLM processing using Ollama (no cloud calls)
- Structured Minutes of Meeting output:
  - Meeting summary
  - Key topics
  - Decisions
  - Action items with owners and deadlines
- Chunking support for long meetings
- Real upload progress bar in the UI
- Deterministic UI states (uploading → processing → results)
- Memory-safe handling of large files

---

## Architecture Overview

Browser uploads file (streamed, no RAM spike)
→ FastAPI backend
→ Optional audio extraction (ffmpeg)
→ Whisper transcription (GPU)
→ GPU memory release
→ Short meetings: single Ollama call
→ Long meetings:
   - transcript chunking
   - per-chunk fact extraction
   - deterministic merge
   - final synthesis call

---

## Tech Stack

Backend:
- Python 3.10+
- FastAPI
- Whisper (GPU)
- Ollama
- ffmpeg / ffmpeg-python

Frontend:
- HTML
- Tailwind CSS
- Vanilla JavaScript
- XMLHttpRequest (for real upload progress)

---

## Supported File Types

Audio:
- .wav
- .mp3
- .m4a

Video:
- .mp4
- .webm
- .mkv

Video files are automatically converted to mono 16kHz audio before transcription.

---

## Upload Limits and Safety

To prevent system crashes on laptops:
- Uploads are streamed to disk (not loaded into RAM)
- Hard upload size limit: 600 MB
- Video files are deleted immediately after audio extraction
- GPU and Python memory are explicitly released after transcription

Attempting to process multi-gigabyte video files on a laptop is not supported.

---

## Hardware Requirements

Minimum (development laptop):
- 24 GB RAM recommended
- NVIDIA GPU with at least 8 GB VRAM
- SSD storage

For larger files and heavy usage, run on a server.

---

## Running the App

1. Activate your virtual environment
2. Ensure ffmpeg is installed and available on PATH
3. Start Ollama with the required model
4. Run the FastAPI app using:

   python -m uvicorn app.main:app --reload

5. Open the browser at http://localhost:8000

---

## Output Format

The backend returns structured JSON containing:
- meeting_summary
- key_topics
- decisions
- tasks

The frontend renders this into a readable Minutes of Meeting view.

---

## Notes

- This project prioritizes correctness and safety over aggressive summarization
- Long municipal meetings are handled conservatively to avoid hallucination
- Chunking is automatically enabled for long transcripts

---

## License

MIT License
