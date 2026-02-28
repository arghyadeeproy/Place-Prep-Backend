import json
import re
from groq import Groq
from django.conf import settings


client = Groq(api_key=settings.GROQ_API_KEY)

MODEL = "llama-3.3-70b-versatile"   # Best balance for quality + JSON


def _clean_json(raw: str) -> str:
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


# ─────────────────────────────────────────
# Company Guide
# ─────────────────────────────────────────

def generate_company_guide(company_name: str) -> dict:
    prompt = f"""
You are a placement preparation expert.
Generate a structured interview guide for {company_name}.

Return ONLY valid JSON.

Schema:
{{
  "name": "{company_name}",
  "tagline": "...",
  "about": "...",
  "package": "...",
  "difficulty": "Easy | Medium | Hard",
  "rounds": <integer>,
  "roles": ["..."],
  "rounds_detail_list": [
    {{
      "name": "...",
      "type": "OA | Technical | HR | Behavioral",
      "duration": "...",
      "desc": "..."
    }}
  ],
  "pyqs": [
    {{
      "q": "...",
      "tag": "...",
      "difficulty": "...",
      "freq": "High | Medium | Low"
    }}
  ],
  "tips": ["..."],
  "resources": [
    {{ "title": "...", "type": "Practice | Book | Guide" }}
  ]
}}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )

    raw = _clean_json(response.choices[0].message.content)

    try:
        return json.loads(raw)
    except Exception as e:
        raise ValueError(f"Groq invalid JSON: {e}\nRaw: {raw[:400]}")


# ─────────────────────────────────────────
# MCQ Generation
# ─────────────────────────────────────────

def generate_mcq_questions(topic: str, difficulty: str, count: int = 10) -> list:
    prompt = f"""
Generate {count} unique MCQs for topic: {topic}
Difficulty: {difficulty}

Return ONLY JSON array:

[
  {{
    "question": "...",
    "options": ["A","B","C","D"],
    "answer": 0,
    "explanation": "...",
    "tag": "{topic}",
    "difficulty": "{difficulty}",
    "type": "conceptual | numerical | code-output | scenario"
  }}
]
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
    )

    raw = _clean_json(response.choices[0].message.content)

    try:
        questions = json.loads(raw)
    except Exception as e:
        raise ValueError(f"Groq bad JSON: {e}\nRaw: {raw[:400]}")

    if not isinstance(questions, list):
        raise ValueError("Expected list of questions")

    return questions