"""
api/views/skilltest_views.py
─────────────────────────────
Dynamic Gemini MCQ flow:

  POST /api/skilltest/generate/
       → Gemini generates N fresh questions (temperature=0.9 → unique every time)
       → SESSION saved to Firestore with answers locked server-side
       → Client gets questions WITHOUT answers

  POST /api/skilltest/submit/<session_id>/
       → Client sends { "answers": {"0":1, "1":3, ...}, "time_taken_seconds": 250 }
       → Backend grades against locked answers
       → Returns full result with explanations
       → Session marked completed — no re-submission
"""

import uuid
from datetime import datetime, timezone, timedelta

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from google.cloud import firestore as gfs

from api.firebase import db, SERVER_TS, Collections, doc_to_dict, query_to_list
from api.groq_ai import generate_mcq_questions
from api.utils import success, get_uid, get_user_info


TOPICS = [
    {"id": "DSA",          "label": "Data Structures & Algorithms", "icon": "🌲", "color": "#FFD600"},
    {"id": "DBMS",         "label": "Database Management Systems",  "icon": "🗄️",  "color": "#54a0ff"},
    {"id": "OS",           "label": "Operating Systems",            "icon": "⚙️",   "color": "#ff9f43"},
    {"id": "CN",           "label": "Computer Networks",            "icon": "🌐",  "color": "#1dd1a1"},
    {"id": "OOPs",         "label": "Object-Oriented Programming",  "icon": "🧩",  "color": "#a29bfe"},
    {"id": "Aptitude",     "label": "Quantitative Aptitude",        "icon": "🔢",  "color": "#fd79a8"},
    {"id": "SQL",          "label": "SQL & Query Writing",          "icon": "📊",  "color": "#00cec9"},
    {"id": "Python",       "label": "Python Programming",           "icon": "🐍",  "color": "#6c5ce7"},
    {"id": "Java",         "label": "Java Programming",             "icon": "☕",   "color": "#e17055"},
    {"id": "SystemDesign", "label": "System Design",                "icon": "🏗️",   "color": "#fdcb6e"},
]

VALID_TOPICS       = {t["id"] for t in TOPICS}
VALID_DIFFICULTIES = {"Easy", "Medium", "Hard"}
SESSION_TTL_HOURS  = 2


def _strip_answers(questions: list) -> list:
    """Return client-safe question list — no answer index, no explanation."""
    return [
        {
            "index":      i,
            "question":   q["question"],
            "options":    q["options"],
            "tag":        q.get("tag", ""),
            "difficulty": q.get("difficulty", ""),
            "type":       q.get("type", "conceptual"),
        }
        for i, q in enumerate(questions)
    ]


# ── Topics ────────────────────────────────────────────────────────────────────

class TopicsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success(TOPICS)


# ── Generate ──────────────────────────────────────────────────────────────────

class GenerateTestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        topic      = str(request.data.get("topic", "DSA")).strip()
        difficulty = str(request.data.get("difficulty", "Medium")).strip()
        count      = int(request.data.get("count", 10))

        if topic not in VALID_TOPICS:
            return Response({"error": True, "detail": f"Invalid topic. Choose from: {', '.join(sorted(VALID_TOPICS))}"}, status=400)
        if difficulty not in VALID_DIFFICULTIES:
            return Response({"error": True, "detail": "Invalid difficulty. Choose: Easy, Medium, Hard."}, status=400)
        count = max(5, min(count, 20))

        # Generate via Gemini
        try:
            questions = generate_mcq_questions(topic=topic, difficulty=difficulty, count=count)
        except ValueError as e:
            return Response({"error": True, "detail": str(e)}, status=502)
        except Exception as e:
            return Response({"error": True, "detail": f"AI generation failed: {str(e)}"}, status=502)

        session_id = uuid.uuid4().hex[:20]
        user       = get_user_info(request)
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=SESSION_TTL_HOURS)).isoformat()

        # Save session — includes full questions WITH answers (never sent to client)
        db.collection(Collections.ACTIVE_SESSIONS).document(session_id).set({
            "session_id":   session_id,
            "user_uid":     user["uid"],
            "user_name":    user["name"],
            "topic":        topic,
            "difficulty":   difficulty,
            "count":        len(questions),
            "questions":    questions,
            "time_minutes": max(5, count),
            "created_at":   SERVER_TS,
            "expires_at":   expires_at,
            "completed":    False,
        })

        return success({
            "session_id":   session_id,
            "topic":        topic,
            "difficulty":   difficulty,
            "count":        len(questions),
            "time_minutes": max(5, count),
            "questions":    _strip_answers(questions),   # ← no answers
        }, status_code=201)


# ── Submit ────────────────────────────────────────────────────────────────────

class SubmitSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id: str):
        answers    = request.data.get("answers", {})      # {"0": 1, "1": 3, ...}
        time_taken = int(request.data.get("time_taken_seconds", 0))

        if not isinstance(answers, dict):
            return Response({"error": True, "detail": "'answers' must be an object."}, status=400)

        session_ref = db.collection(Collections.ACTIVE_SESSIONS).document(session_id)
        session_doc = doc_to_dict(session_ref.get())

        if not session_doc:
            return Response({"error": True, "detail": "Session not found or expired."}, status=404)

        uid = get_uid(request)
        if session_doc["user_uid"] != uid:
            return Response({"error": True, "detail": "Forbidden."}, status=403)

        if session_doc.get("completed"):
            return Response({"error": True, "detail": "Already submitted."}, status=400)

        # Check TTL
        try:
            exp = datetime.fromisoformat(session_doc["expires_at"])
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > exp:
                return Response({"error": True, "detail": "Session expired."}, status=410)
        except Exception:
            pass

        # Grade
        questions = session_doc["questions"]
        total = len(questions)
        correct = wrong = skipped = 0
        results = []

        for i, q in enumerate(questions):
            user_ans    = answers.get(str(i))
            correct_ans = int(q["answer"])

            if user_ans is None:
                verdict = "skipped"; skipped += 1
            elif int(user_ans) == correct_ans:
                verdict = "correct"; correct += 1
            else:
                verdict = "wrong";   wrong += 1

            results.append({
                "index":          i,
                "question":       q["question"],
                "options":        q["options"],
                "tag":            q.get("tag", ""),
                "difficulty":     q.get("difficulty", ""),
                "type":           q.get("type", "conceptual"),
                "user_answer":    int(user_ans) if user_ans is not None else None,
                "correct_answer": correct_ans,
                "explanation":    q.get("explanation", ""),
                "verdict":        verdict,
            })

        score_pct = round((correct / total) * 100) if total else 0
        grade = (
            "🏆 Excellent"       if score_pct >= 80 else
            "👍 Good"            if score_pct >= 60 else
            "💪 Keep Practicing"
        )
        user = get_user_info(request)

        # Save attempt
        attempt_ref = db.collection(Collections.TEST_ATTEMPTS).document()
        attempt_ref.set({
            "session_id":         session_id,
            "user_uid":           uid,
            "user_name":          user["name"],
            "topic":              session_doc["topic"],
            "difficulty":         session_doc["difficulty"],
            "total_questions":    total,
            "correct":            correct,
            "wrong":              wrong,
            "skipped":            skipped,
            "score_pct":          score_pct,
            "grade":              grade,
            "time_taken_seconds": time_taken,
            "submitted_at":       SERVER_TS,
        })

        # Mark session complete + update user stats
        session_ref.update({"completed": True, "attempt_id": attempt_ref.id})
        db.collection(Collections.USERS).document(uid).update({
            "stats.tests_taken": gfs.Increment(1),
            "stats.total_score": gfs.Increment(score_pct),
        })

        return success({
            "attempt_id": attempt_ref.id,
            "session_id": session_id,
            "topic":      session_doc["topic"],
            "difficulty": session_doc["difficulty"],
            "total":      total,
            "correct":    correct,
            "wrong":      wrong,
            "skipped":    skipped,
            "score_pct":  score_pct,
            "grade":      grade,
            "time_taken": time_taken,
            "results":    results,
        })


# ── Attempt History ───────────────────────────────────────────────────────────

class AttemptHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        uid = get_uid(request)
        attempts = query_to_list(
            db.collection(Collections.TEST_ATTEMPTS)
            .where("user_uid", "==", uid)
            .order_by("submitted_at", direction=gfs.Query.DESCENDING)
            .limit(50)
        )
        return success(attempts)


# ── Leaderboard ───────────────────────────────────────────────────────────────

class LeaderboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        topic      = request.query_params.get("topic", "")
        difficulty = request.query_params.get("difficulty", "")

        query = db.collection(Collections.TEST_ATTEMPTS)
        if topic:      query = query.where("topic", "==", topic)
        if difficulty: query = query.where("difficulty", "==", difficulty)

        attempts = query_to_list(
            query.order_by("score_pct", direction=gfs.Query.DESCENDING)
                 .order_by("time_taken_seconds")
                 .limit(50)
        )

        seen  = set()
        board = []
        for a in attempts:
            if a["user_uid"] in seen:
                continue
            seen.add(a["user_uid"])
            board.append({
                "rank":       len(board) + 1,
                "user_name":  a.get("user_name"),
                "score_pct":  a.get("score_pct"),
                "grade":      a.get("grade"),
                "time_taken": a.get("time_taken_seconds"),
                "topic":      a.get("topic"),
                "difficulty": a.get("difficulty"),
            })
            if len(board) == 10:
                break

        return success(board)