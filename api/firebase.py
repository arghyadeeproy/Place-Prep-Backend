"""
api/firebase.py
Initialises Firebase Admin SDK safely for:
- Render production (FIREBASE_CREDENTIALS_JSON)
- Local development (firebase_credentials.json file)
"""

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, auth
from django.conf import settings


def _init_firebase():
    if firebase_admin._apps:
        return

    # 1️⃣ Production (Render)
    firebase_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")

    if firebase_json:
        try:
            cred_dict = json.loads(firebase_json)
            cred = credentials.Certificate(cred_dict)
        except Exception as e:
            raise Exception(f"Invalid FIREBASE_CREDENTIALS_JSON: {e}")

    else:
        # 2️⃣ Local development (JSON file)
        cred_path = getattr(
            settings,
            "FIREBASE_CREDENTIALS_PATH",
            "firebase_credentials.json"
        )

        if not os.path.exists(cred_path):
            raise Exception(
                "Firebase credentials not found. "
                "Set FIREBASE_CREDENTIALS_JSON (production) "
                "or provide firebase_credentials.json (local)."
            )

        cred = credentials.Certificate(cred_path)

    project_id = getattr(settings, "FIREBASE_PROJECT_ID", None)

    if not project_id:
        raise Exception("FIREBASE_PROJECT_ID is not set in environment")

    firebase_admin.initialize_app(
        cred,
        {"projectId": project_id},
    )


_init_firebase()

# Firestore + Auth clients
db = firestore.client()
firebase_auth = auth
SERVER_TS = firestore.SERVER_TIMESTAMP


class Collections:
    USERS = "users"
    TEST_ATTEMPTS = "test_attempts"
    ACTIVE_SESSIONS = "active_sessions"
    POSTS = "posts"
    COMPANY_CACHE = "company_cache"


def doc_to_dict(doc):
    if not doc.exists:
        return None
    data = doc.to_dict()
    data["id"] = doc.id
    return data


def query_to_list(query):
    return [doc_to_dict(d) for d in query.stream()]