from faster_whisper import WhisperModel

# Load ONCE at startup
whisper_model = WhisperModel(
    "small",
    device="cuda",
    compute_type="int8_float16"
)

def transcribe(audio_path: str) -> str:
    segments, _ = whisper_model.transcribe(
        audio_path,
        beam_size=5,
        vad_filter=True
    )

    return " ".join(segment.text.strip() for segment in segments)

import torch

def release_gpu():
    torch.cuda.empty_cache()
    
from app.whisper_gpu import transcribe

print(transcribe("test.wav"))
