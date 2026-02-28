"""api/views/placement_views.py — Company placement guides powered by Groq."""

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.firebase import db, SERVER_TS, Collections, doc_to_dict
from api.groq_ai import generate_company_guide
from api.utils import success


# ── Bump this whenever the prompt quality is improved. ────────────────────────
# Any cached guide whose cache_version < CURRENT_CACHE_VERSION will be
# automatically re-generated on the next GET, so stale low-quality guides
# (e.g. with generic PYQs) are replaced transparently.
CURRENT_CACHE_VERSION = 2   # ← increment when prompt changes


POPULAR = [
    {"id": "google",     "name": "Google",        "color": "#4285F4", "logo": "G"},
    {"id": "amazon",     "name": "Amazon",         "color": "#FF9900", "logo": "A"},
    {"id": "microsoft",  "name": "Microsoft",      "color": "#00a4ef", "logo": "M"},
    {"id": "meta",       "name": "Meta",           "color": "#1877F2", "logo": "M"},
    {"id": "flipkart",   "name": "Flipkart",       "color": "#FFD600", "logo": "F"},
    {"id": "adobe",      "name": "Adobe",          "color": "#FF0000", "logo": "A"},
    {"id": "oracle",     "name": "Oracle",         "color": "#F80000", "logo": "O"},
    {"id": "infosys",    "name": "Infosys",        "color": "#007CC5", "logo": "I"},
    {"id": "tcs",        "name": "TCS",            "color": "#CC0000", "logo": "T"},
    {"id": "wipro",      "name": "Wipro",          "color": "#5F259F", "logo": "W"},
    {"id": "goldman",    "name": "Goldman Sachs",  "color": "#7399C6", "logo": "GS"},
    {"id": "deshaw",     "name": "D.E. Shaw",      "color": "#00B4D8", "logo": "DE"},
    {"id": "swiggy",     "name": "Swiggy",         "color": "#FC8019", "logo": "S"},
    {"id": "zomato",     "name": "Zomato",         "color": "#E23744", "logo": "Z"},
    {"id": "paytm",      "name": "Paytm",          "color": "#00BAF2", "logo": "P"},
    {"id": "phonepe",    "name": "PhonePe",        "color": "#5F259F", "logo": "P"},
    {"id": "deloitte",   "name": "Deloitte",       "color": "#86BC25", "logo": "D"},
    {"id": "capgemini",  "name": "Capgemini",      "color": "#0070AD", "logo": "C"},
    {"id": "accenture",  "name": "Accenture",      "color": "#A100FF", "logo": "A"},
]


def _id_to_name(company_id: str) -> str:
    for c in POPULAR:
        if c["id"] == company_id:
            return c["name"]
    return company_id.replace("-", " ").title()


class PopularCompaniesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success(POPULAR)


class CompanyGuideView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id: str):
        company_id = company_id.lower().strip()

        # 1. Check Firestore cache — but only use it if cache_version is current.
        #    Stale guides (old prompt version) are silently re-generated.
        cache_ref = db.collection(Collections.COMPANY_CACHE).document(company_id)
        cached    = doc_to_dict(cache_ref.get())

        if cached and cached.get("cache_version", 0) >= CURRENT_CACHE_VERSION:
            cached.pop("_cached_at", None)
            cached.pop("cache_version", None)
            return success(cached)

        # 2. Generate via Groq (stale or missing cache both reach here)
        try:
            guide = generate_company_guide(_id_to_name(company_id))
        except ValueError as e:
            # If we have a stale cached guide, return it rather than erroring
            if cached:
                cached.pop("_cached_at", None)
                cached.pop("cache_version", None)
                return success(cached)
            return Response({"error": True, "detail": str(e)}, status=502)
        except Exception as e:
            if cached:
                cached.pop("_cached_at", None)
                cached.pop("cache_version", None)
                return success(cached)
            return Response({"error": True, "detail": f"AI generation failed: {str(e)}"}, status=502)

        # 3. Write to cache with current version stamp
        guide["_cached_at"]    = SERVER_TS
        guide["cache_version"] = CURRENT_CACHE_VERSION
        guide["company_id"]    = company_id
        cache_ref.set(guide)

        guide.pop("_cached_at", None)
        guide.pop("cache_version", None)
        return success(guide)


class CompanyCacheRefreshView(APIView):
    """DELETE to force-regenerate the Groq cache for a specific company."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, company_id: str):
        company_id = company_id.lower().strip()
        db.collection(Collections.COMPANY_CACHE).document(company_id).delete()
        return success(message=f"Cache cleared for '{company_id}'. Next GET will regenerate.")


class CompanyCacheRefreshAllView(APIView):
    """DELETE /api/placement/cache/refresh-all/ — wipe ALL cached guides.
       Use this after bumping CURRENT_CACHE_VERSION to force a full refresh."""
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        docs = db.collection(Collections.COMPANY_CACHE).stream()
        count = 0
        for doc in docs:
            doc.reference.delete()
            count += 1
        return success(message=f"Cleared {count} cached company guides. All will regenerate on next visit.")