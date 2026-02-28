from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from firebase_admin import auth as firebase_auth
from google.cloud import firestore as gfs

from api.firebase import db, Collections, SERVER_TS


class FirebaseUser:
    def __init__(self, decoded_token):
        self.uid = (
            decoded_token.get("uid")
            or decoded_token.get("user_id")
            or decoded_token.get("sub")
        )
        self.email = decoded_token.get("email")
        self.name = decoded_token.get("name") or "User"
        self.picture = decoded_token.get("picture")
        self.provider = decoded_token.get("firebase", {}).get("sign_in_provider")
        self.is_authenticated = True

    def __str__(self):
        return self.uid


class FirebaseAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return None

        try:
            prefix, token = auth_header.split()
            if prefix.lower() != "bearer":
                raise AuthenticationFailed("Invalid token prefix")
        except ValueError:
            raise AuthenticationFailed("Invalid Authorization header format")

        try:
            decoded_token = firebase_auth.verify_id_token(token)
        except Exception:
            raise AuthenticationFailed("Invalid or expired Firebase token")

        user = FirebaseUser(decoded_token)

        # 🔥 Auto-create Firestore user document if not exists
        user_ref = db.collection(Collections.USERS).document(user.uid)
        snapshot = user_ref.get()

        if not snapshot.exists:
            user_ref.set({
                "uid": user.uid,
                "email": user.email,
                "name": user.name,
                "profile_picture": user.picture,
                "provider": user.provider,
                "created_at": SERVER_TS,
                "stats": {
                    "posts": 0,
                    "comments": 0,
                    "tests_taken": 0,
                    "total_score": 0,
                    "modules_done": 0,
                }
            })

        return (user, decoded_token)