"""api/views/dashboard_views.py — Aggregated dashboard for the logged-in user."""

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from google.cloud import firestore as gfs
from collections import defaultdict
from datetime import datetime, timezone, timedelta

from api.firebase import db, Collections, doc_to_dict, query_to_list
from api.utils import success, get_uid


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        uid = get_uid(request)

        # ── User profile ──────────────────────────────────────────────────────
        user_doc = doc_to_dict(db.collection(Collections.USERS).document(uid).get())
        if not user_doc:
            return Response({"error": True, "detail": "User not found."}, status=404)

        # ── Test attempts ─────────────────────────────────────────────────────
        attempts = query_to_list(
            db.collection(Collections.TEST_ATTEMPTS)
            .where("user_uid", "==", uid)
            .order_by("submitted_at", direction=gfs.Query.DESCENDING)
            .limit(100)
        )

        total_correct   = 0
        total_attempted = 0
        score_sum       = 0
        best_score      = 0
        tag_correct     = defaultdict(int)
        tag_total       = defaultdict(int)
        score_trend     = []
        now             = datetime.now(timezone.utc)
        week_ago        = now - timedelta(days=7)
        tests_this_week = 0

        for a in attempts:
            total_correct   += a.get("correct", 0)
            total_attempted += a.get("total_questions", 0)
            score_sum       += a.get("score_pct", 0)
            best_score       = max(best_score, a.get("score_pct", 0))
            tag = a.get("topic", "Other")
            tag_correct[tag] += a.get("correct", 0)
            tag_total[tag]   += a.get("total_questions", 0)

            ts = a.get("submitted_at")
            if ts:
                try:
                    dt = ts if isinstance(ts, datetime) else ts.astimezone(timezone.utc)
                    if dt > week_ago:
                        tests_this_week += 1
                    score_trend.append({"date": dt.strftime("%b %d"), "score": a.get("score_pct", 0)})
                except Exception:
                    pass

        avg_score  = round(score_sum / len(attempts)) if attempts else 0
        accuracy   = round((total_correct / total_attempted) * 100) if total_attempted else 0
        tag_perf   = {
            tag: round((tag_correct[tag] / tag_total[tag]) * 100)
            for tag in tag_total if tag_total[tag]
        }

        # ── Recent posts ──────────────────────────────────────────────────────
        recent_posts = query_to_list(
            db.collection(Collections.POSTS)
            .where("author_uid", "==", uid)
            .order_by("created_at", direction=gfs.Query.DESCENDING)
            .limit(3)
        )
        for p in recent_posts:
            p.pop("likes", None)

        # ── Platform counts ───────────────────────────────────────────────────
        total_users  = len(query_to_list(db.collection(Collections.USERS).limit(5000)))
        total_posts  = len(query_to_list(db.collection(Collections.POSTS).limit(2000)))
        total_guides = len(query_to_list(db.collection(Collections.COMPANY_CACHE).limit(500)))

        user_stats = user_doc.get("stats", {})

        return success({
            "user": {
                "uid":      user_doc.get("uid"),
                "name":     user_doc.get("name"),
                "email":    user_doc.get("email"),
                "initials": user_doc.get("initials"),
                "college":  user_doc.get("college"),
                "branch":   user_doc.get("branch"),
                "year":     user_doc.get("year"),
            },
            "stats": {
                # SkillTest
                "tests_taken":               len(attempts),
                "avg_score":                 avg_score,
                "best_score":                best_score,
                "tests_this_week":           tests_this_week,
                "total_questions_attempted": total_attempted,
                "correct_answers":           total_correct,
                "accuracy_pct":              accuracy,
                # Community
                "posts_created":             user_stats.get("posts", 0),
                "comments_posted":           user_stats.get("comments", 0),
                # Study
                "modules_done":              user_stats.get("modules_done", 0),
            },
            "recent_attempts":  attempts[:5],
            "score_trend":      score_trend[:7],
            "tag_performance":  tag_perf,
            "recent_posts":     recent_posts,
            "platform": {
                "total_users":         total_users,
                "total_posts":         total_posts,
                "company_guides":      total_guides,
                "topics_available":    10,
            },
        })