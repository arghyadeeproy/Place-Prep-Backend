"""api/utils.py — Shared response helpers."""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed


# ── Exception Handler ─────────────────────────────────────────

def custom_exception_handler(exc, context):
    """Wrap all DRF errors in a consistent {error, detail} envelope."""
    response = exception_handler(exc, context)

    if response is not None:
        return Response(
            {"error": True, "detail": response.data},
            status=response.status_code
        )

    return Response(
        {"error": True, "detail": "Internal server error."},
        status=500
    )


# ── Success Helper ────────────────────────────────────────────

def success(data=None, message="OK", status_code=200):
    payload = {"error": False, "message": message}

    if data is not None:
        payload["data"] = data

    return Response(payload, status=status_code)


# ── Pagination ────────────────────────────────────────────────

def paginate(items, page=1, page_size=20):
    total = len(items)
    start = (page - 1) * page_size
    end   = start + page_size

    return {
        "results":   items[start:end],
        "count":     total,
        "page":      page,
        "page_size": page_size,
        "has_next":  end < total,
    }


# ── Firebase Auth Helpers ─────────────────────────────────────

def get_uid(request) -> str:
    return getattr(request.user, "uid", None)


def get_user_info(request) -> dict:
    """
    Extract user info from FirebaseUser object.
    """
    user = request.user

    if not user:
        raise AuthenticationFailed("Invalid authentication state")

    return {
        "uid": getattr(user, "uid", None),
        "name": getattr(user, "name", "Anonymous"),
        "initials": getattr(user, "name", "A")[0].upper() if getattr(user, "name", None) else "??",
    }