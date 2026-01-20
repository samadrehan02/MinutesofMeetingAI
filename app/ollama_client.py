import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1:8b-instruct-q4_K_M"

def extract_minutes(transcript: str) -> str:
    prompt = f"""
You are a technical secretary. Extract highly detailed Minutes of Meeting.

IMPORTANT:
- key_topics MUST be an array of strings
- decisions MUST be an array of strings
- DO NOT use objects for key_topics or decisions

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

def extract_chunk_summary(transcript_chunk: str) -> dict:
    prompt = f"""
You extract meeting information from a PARTIAL transcript.

IMPORTANT:
- key_topics MUST be an array of strings
- decisions MUST be an array of strings
- DO NOT use objects for key_topics or decisions

Return ONLY valid JSON.

Schema:
{{
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

Transcript chunk:
\"\"\"{transcript_chunk}\"\"\"
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

def aggregate_minutes(chunks: list[dict]) -> dict:
    prompt = f"""
You combine multiple partial meeting summaries into final Minutes of Meeting.

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

Partial summaries:
{chunks}
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

def normalize_partials(partials: list[dict]) -> list[dict]:
    cleaned = []

    for p in partials:
        cleaned.append({
            "key_topics": list(map(str, p.get("key_topics", []))),
            "decisions": list(map(str, p.get("decisions", []))),
            "tasks": p.get("tasks", [])
        })

    return cleaned
