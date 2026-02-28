"""
api/firebase.py
Initialises Firebase Admin SDK once.
"""

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, auth
from django.conf import settings


def _init_firebase():
    if firebase_admin._apps:
        return

    firebase_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")

    if firebase_json:
        # Production (Render)
        cred = credentials.Certificate(json.loads(firebase_json))
    else:
        # Local development
        cred_path = getattr(settings, "FIREBASE_CREDENTIALS_PATH", "firebase_credentials.json")

        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
        else:
            cred = credentials.ApplicationDefault()

    firebase_admin.initialize_app(
        cred,
        {"projectId": getattr(settings, "FIREBASE_PROJECT_ID", None)},
    )


_init_firebase()

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