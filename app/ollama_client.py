import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1:8b-instruct-q4_K_M"


def extract_minutes(transcript: str) -> str:
    prompt = f"""
You are a technical secretary. Extract detailed Minutes of Meeting.

IMPORTANT RULES:
- Use ONLY information explicitly present in the transcript.
- Do NOT invent technical details.
- If something is discussed vaguely, summarize it vaguely.
- If unsure, omit the detail.

Return ONLY valid JSON.

Schema:
{{
  "meeting_summary": "3–4 sentence comprehensive overview",
  "key_topics": [
    {{
      "topic": "Concise topic title",
      "details": "1–2 sentences explaining what was discussed"
    }}
  ],
  "decisions": [
    {{
      "decision": "What was decided",
      "rationale": "Why it was decided"
    }}
  ],
  "tasks": [
    {{
      "description": "Clear action item",
      "owner": "Person or team responsible, or Unassigned",
      "deadline": "Deadline if mentioned, otherwise N/A"
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

    # Ollama returns JSON as a string in "response"
    return resp.json()["response"]
