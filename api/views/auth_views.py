# api/views/auth_views.py — Authentication views.

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.firebase import db, firebase_auth, SERVER_TS, Collections, doc_to_dict
from api.utils import success, get_uid


def _make_initials(name: str) -> str:
    parts = name.strip().split()
    return "".join(p[0].upper() for p in parts[:2]) if parts else "??"


class RegisterView(APIView):
    """
    Called AFTER the client has already created the Firebase Auth user.
    We only need to create the Firestore profile document here.
    The Firebase Auth user creation is handled client-side.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        name     = request.data.get("name", "").strip()
        email    = request.data.get("email", "").lower().strip()
        password = request.data.get("password", "")  # only used for length validation

        try:
            year = int(request.data.get("year", 1))
        except (ValueError, TypeError):
            return Response({"error": True, "detail": "Year must be a number."}, status=400)

        if not name or not email or not password:
            return Response(
                {"error": True, "detail": "name, email and password are required."},
                status=400
            )

        if len(password) < 6:
            return Response(
                {"error": True, "detail": "Password must be at least 6 characters."},
                status=400
            )

        # Look up the Firebase Auth user by email (already created client-side)
        try:
            fb_user = firebase_auth.get_user_by_email(email)
            uid = fb_user.uid
        except firebase_auth.UserNotFoundError:
            return Response(
                {"error": True, "detail": "Firebase user not found. Complete client-side signup first."},
                status=400
            )
        except Exception as e:
            return Response({"error": True, "detail": f"Auth lookup failed: {str(e)}"}, status=400)

        # Check if Firestore profile already exists
        existing_doc = db.collection(Collections.USERS).document(uid).get()
        if existing_doc.exists:
            return Response(
                {"error": True, "detail": "An account with this email already exists."},
                status=400
            )

        college = request.data.get("college", "").strip()
        branch  = request.data.get("branch", "").strip()

        user_doc = {
            "uid":        uid,
            "name":       name,
            "email":      email,
            "initials":   _make_initials(name),
            "college":    college,
            "branch":     branch,
            "year":       year,
            "created_at": SERVER_TS,
            "last_login": SERVER_TS,
            "stats": {
                "tests_taken":  0,
                "total_score":  0,
                "posts":        0,
                "comments":     0,
                "modules_done": 0,
            },
        }

        try:
            db.collection(Collections.USERS).document(uid).set(user_doc)
        except Exception as e:
            return Response({"error": True, "detail": f"Profile creation failed: {str(e)}"}, status=400)

        return success(
            {"uid": uid, "email": email, "name": name},
            message="Account created successfully.",
            status_code=201,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        id_token = request.data.get("id_token")

        if not id_token:
            return Response({"error": True, "detail": "ID token required."}, status=400)

        try:
            decoded = firebase_auth.verify_id_token(id_token)
            uid = decoded["uid"]
        except Exception:
            return Response({"error": True, "detail": "Invalid token."}, status=401)

        # ⚠️ Removed email_verified check — blocks Google users and freshly-registered
        # email users who haven't yet verified. Handle verification in the frontend if needed.

        user_doc = doc_to_dict(db.collection(Collections.USERS).document(uid).get())

        if not user_doc:
            return Response({"error": True, "detail": "User profile not found."}, status=404)

        db.collection(Collections.USERS).document(uid).update({"last_login": SERVER_TS})

        return success({"user": user_doc}, message="Login successful.")


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        uid = get_uid(request)
        try:
            doc = doc_to_dict(db.collection(Collections.USERS).document(uid).get())
        except Exception:
            return Response({"error": True, "detail": "Failed to fetch profile."}, status=500)

        if not doc:
            return Response({"error": True, "detail": "Profile not found."}, status=404)

        doc.pop("password_hash", None)
        return success(doc)

    def patch(self, request):
        uid = get_uid(request)
        allowed_fields = ("name", "college", "branch", "year")
        update_data = {k: v for k, v in request.data.items() if k in allowed_fields}

        if not update_data:
            return Response({"error": True, "detail": "No valid fields to update."}, status=400)

        if "year" in update_data:
            try:
                update_data["year"] = int(update_data["year"])
            except (ValueError, TypeError):
                return Response({"error": True, "detail": "Year must be a number."}, status=400)

        if "name" in update_data:
            name = update_data["name"].strip()
            if not name:
                return Response({"error": True, "detail": "Name cannot be empty."}, status=400)
            update_data["name"] = name
            update_data["initials"] = _make_initials(name)

        try:
            db.collection(Collections.USERS).document(uid).update(update_data)
        except Exception:
            return Response({"error": True, "detail": "Failed to update profile."}, status=500)

        return success(update_data, message="Profile updated.")