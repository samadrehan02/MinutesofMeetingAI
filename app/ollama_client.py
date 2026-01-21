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

def extract_chunk_facts(chunk: str) -> str:
    prompt = f"""
Extract ONLY factual information from the following meeting transcript chunk.

Rules:
- Do NOT summarize
- Do NOT explain
- Do NOT invent information
- If nothing is present, return empty arrays

Return ONLY valid JSON.

Schema:
{{
  "topics": [string],
  "decisions": [string],
  "tasks": [
    {{
      "description": string,
      "owner": string|null,
      "deadline": string|null
    }}
  ]
}}

Transcript chunk:
\"\"\"{chunk}\"\"\"
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

def synthesize_minutes(topics, decisions, tasks) -> str:
    prompt = f"""
You are generating FINAL Minutes of Meeting for a municipal council meeting.

Your task is to CONSOLIDATE, ABSTRACT, and EXPAND raw meeting facts into
professional, detailed minutes suitable for public record.

IMPORTANT:
This is a long meeting covering multiple agenda items.

Do NOT overly compress the output.
Prefer completeness over brevity.
If multiple approvals or discussions occurred, list them separately.
It is acceptable to include many topics and decisions.

CRITICAL RULES:
- Use ONLY the provided data
- Do NOT invent facts, numbers, conditions, or names
- Do NOT speculate beyond the provided material
- Remove exact duplicates, but PRESERVE important detail
- If conditions are mentioned, describe them at a high level
- If approvals are mentioned, explain what was approved and why
- Group similar items only when they clearly refer to the same agenda item

Meeting Summary:
- Write a detailed 5–7 sentence summary
- Mention the types of applications reviewed
- Mention major approvals and unanimous decisions
- Mention public hearings and rezonings explicitly

Key Topics:
- Use high-level topic names
- Under each topic, explain:
  - what was discussed
  - what applications or permits were involved
  - what the outcome was
- Include contextual details (locations, business type, purpose) if present

Decisions:
- Each decision must:
  - clearly state WHAT was approved
  - include CONDITIONS at a descriptive level
  - mention whether it was unanimous if stated
- Avoid repeating the same decision wording

Action Items:
- Describe the task clearly and completely
- Preserve owners if named
- Clarify what must be done and why, if stated
- Use "Unassigned" only if no owner is mentioned
- Use "N/A" only if no deadline is stated

Ignore empty, null, or placeholder entries.

Return ONLY valid JSON.

Schema:
{{
  "meeting_summary": string,
  "key_topics": [
    {{
      "topic": string,
      "details": string
    }}
  ],
  "decisions": [
    {{
      "decision": string,
      "rationale": string
    }}
  ],
  "tasks": [
    {{
      "description": string,
      "owner": string,
      "deadline": string
    }}
  ]
}}

Raw Topics:
{topics}

Raw Decisions:
{decisions}

Raw Tasks:
{tasks}
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
