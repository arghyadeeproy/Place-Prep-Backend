# """
# api/gemini.py
# Modern Gemini integration using google-genai SDK
# """

# import json
# import re
# from google import genai
# from django.conf import settings


# # ─────────────────────────────────────────────────────
# # Client
# # ─────────────────────────────────────────────────────

# client = genai.Client(api_key=settings.GEMINI_API_KEY)


# def _clean_json(raw: str) -> str:
#     """Strip markdown code fences Gemini sometimes adds."""
#     raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
#     raw = re.sub(r"\s*```$", "", raw)
#     return raw.strip()


# # ─────────────────────────────────────────────────────
# # Company Guide
# # ─────────────────────────────────────────────────────

# COMPANY_GUIDE_PROMPT = """<KEEP YOUR SAME PROMPT HERE>"""


# def generate_company_guide(company_name: str) -> dict:
#     prompt = COMPANY_GUIDE_PROMPT.format(company_name=company_name)

#     try:
#         response = client.models.generate_content(
#             model="gemini-2.0-flash",
#             contents=prompt,
#         )

#         raw = _clean_json(response.text)

#         data = json.loads(raw)

#         if "rounds_detail" in data:
#             data["rounds_detail_list"] = data.pop("rounds_detail")

#         return data

#     except Exception as e:
#         raise ValueError(f"Gemini company guide error: {str(e)}")


# # ─────────────────────────────────────────────────────
# # MCQ Generation
# # ─────────────────────────────────────────────────────

# MCQ_PROMPT = """<KEEP YOUR SAME MCQ PROMPT HERE>"""


# def generate_mcq_questions(topic: str, difficulty: str, count: int = 10) -> list:
#     prompt = MCQ_PROMPT.format(
#         topic=topic,
#         difficulty=difficulty,
#         count=count,
#     )

#     try:
#         response = client.models.generate_content(
#             model="gemini-2.0-flash",
#             contents=prompt,
#         )

#         raw = _clean_json(response.text)
#         questions = json.loads(raw)

#         if not isinstance(questions, list):
#             raise ValueError("Expected JSON array")

#         validated = []

#         for q in questions:
#             if not all(k in q for k in ("question", "options", "answer", "explanation")):
#                 continue

#             validated.append({
#                 "question": str(q["question"]),
#                 "options": [str(o) for o in q["options"]][:4],
#                 "answer": int(q["answer"]),
#                 "explanation": str(q["explanation"]),
#                 "tag": q.get("tag", topic),
#                 "difficulty": q.get("difficulty", difficulty),
#                 "type": q.get("type", "conceptual"),
#             })

#         if not validated:
#             raise ValueError("No valid questions returned")

#         return validated

#     except Exception as e:
#         raise ValueError(f"Gemini MCQ error: {str(e)}")