"""api/views/placement_views.py — Company placement guides powered by Gemini."""

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.firebase import db, SERVER_TS, Collections, doc_to_dict
from api.groq_ai import generate_company_guide
from api.utils import success


POPULAR = [
    {"id": "google",     "name": "Google",       "color": "#4285F4", "logo": "G"},
    {"id": "amazon",     "name": "Amazon",        "color": "#FF9900", "logo": "A"},
    {"id": "microsoft",  "name": "Microsoft",     "color": "#00a4ef", "logo": "M"},
    {"id": "meta",       "name": "Meta",          "color": "#1877F2", "logo": "M"},
    {"id": "flipkart",   "name": "Flipkart",      "color": "#FFD600", "logo": "F"},
    {"id": "adobe",      "name": "Adobe",         "color": "#FF0000", "logo": "A"},
    {"id": "oracle",     "name": "Oracle",        "color": "#F80000", "logo": "O"},
    {"id": "infosys",    "name": "Infosys",       "color": "#007CC5", "logo": "I"},
    {"id": "tcs",        "name": "TCS",           "color": "#CC0000", "logo": "T"},
    {"id": "wipro",      "name": "Wipro",         "color": "#5F259F", "logo": "W"},
    {"id": "goldman",    "name": "Goldman Sachs", "color": "#7399C6", "logo": "GS"},
    {"id": "deshaw",     "name": "D.E. Shaw",     "color": "#00B4D8", "logo": "DE"},
    {"id": "swiggy",     "name": "Swiggy",        "color": "#FC8019", "logo": "S"},
    {"id": "zomato",     "name": "Zomato",        "color": "#E23744", "logo": "Z"},
    {"id": "paytm",      "name": "Paytm",         "color": "#00BAF2", "logo": "P"},
    {"id": "phonepe",    "name": "PhonePe",       "color": "#5F259F", "logo": "P"},
    {"id": "deloitte",   "name": "Deloitte",      "color": "#86BC25", "logo": "D"},
    {"id": "capgemini",  "name": "Capgemini",     "color": "#0070AD", "logo": "C"},
    {"id": "accenture",  "name": "Accenture",     "color": "#A100FF", "logo": "A"},
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

        # 1. Try Firestore cache first
        cache_ref = db.collection(Collections.COMPANY_CACHE).document(company_id)
        cached    = doc_to_dict(cache_ref.get())
        if cached:
            cached.pop("_cached_at", None)
            return success(cached)

        # 2. Generate via Gemini
        try:
            guide = generate_company_guide(_id_to_name(company_id))
        except ValueError as e:
            return Response({"error": True, "detail": str(e)}, status=502)
        except Exception as e:
            return Response({"error": True, "detail": f"AI generation failed: {str(e)}"}, status=502)

        # 3. Cache it
        guide["_cached_at"]  = SERVER_TS
        guide["company_id"]  = company_id
        cache_ref.set(guide)

        guide.pop("_cached_at", None)
        return success(guide)


class CompanyCacheRefreshView(APIView):
    """DELETE to force-regenerate the Gemini cache for a company."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, company_id: str):
        company_id = company_id.lower().strip()
        db.collection(Collections.COMPANY_CACHE).document(company_id).delete()
        return success(message=f"Cache cleared for '{company_id}'. Next GET will regenerate.")