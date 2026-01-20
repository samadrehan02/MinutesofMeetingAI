import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1:8b-instruct-q4_K_M"

def extract_minutes(transcript: str) -> str:
    prompt = f"""
You are a technical secretary. Extract highly detailed Minutes of Meeting.

IMPORTANT RULES:
- Do NOT invent code, APIs, model names, or technical details.
- ONLY include technical terms that appear explicitly in the transcript.
- If a technical detail is discussed vaguely, summarize it vaguely.
- If unsure, omit the detail.

Return ONLY valid JSON.

STRICT CONSTRAINT:
Every technical statement must be directly supported by the transcript.
If a statement cannot be traced to something said, do not include it.

Schema:
{{
  "meeting_summary": "A 3-4 sentence comprehensive overview",
  "key_topics": [
    {{
      "topic": "string",
      "details": "1-2 sentences summarizing what was said, without adding new technical information"
    }}
  ],
  "decisions": [
    {{
      "decision": "string",
      "rationale": "Why this was decided"
    }}
  ],
  "tasks": [
    {{
      "description": "Clear action item with specific goal",
      "owner": "string",
      "deadline": "string"
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
            "temperature": 0,
            "format": "json"
        },
        timeout=120
    )
    return resp.json()["response"]