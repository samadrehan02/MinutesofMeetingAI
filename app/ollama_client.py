import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1:8b-instruct-q4_K_M"

def extract_minutes(transcript: str) -> dict:
    prompt = f"""
You extract Minutes of Meeting.
Return ONLY valid JSON.

Schema:
{{
  "meeting_summary": string,
  "key_topics": string[],
  "decisions": string[],
  "tasks": [
    {{
      "description": string,
      "owner": string|null,
      "deadline": string|null
    }}
  ]
}}

Transcript:
\"\"\"{transcript}\"\"\"
"""

    resp = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "temperature": 0
        },
        timeout=120
    )

    return json.loads(resp.json()["response"])
