"""
api/firebase.py
───────────────
Initialises Firebase Admin SDK once and exposes:
  db          → Firestore client
  firebase_auth → Firebase Auth client
  SERVER_TS   → Firestore server timestamp sentinel
  Collections → all collection name constants
"""

import os
import firebase_admin
from firebase_admin import credentials, firestore, auth
from django.conf import settings


def _init_firebase():
    if not firebase_admin._apps:
        cred_path = settings.FIREBASE_CREDENTIALS_PATH
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
        else:
            cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred, {"projectId": settings.FIREBASE_PROJECT_ID})


_init_firebase()

db            = firestore.client()
firebase_auth = auth
SERVER_TS     = firestore.SERVER_TIMESTAMP


class Collections:
    USERS           = "users"
    TEST_ATTEMPTS   = "test_attempts"
    ACTIVE_SESSIONS = "active_sessions"   # live MCQ sessions, answers locked server-side
    POSTS           = "posts"             # Dev2Dev questions
    COMPANY_CACHE   = "company_cache"     # cached Gemini company guides


def doc_to_dict(doc):
    """Convert Firestore DocumentSnapshot → plain dict with 'id'."""
    if not doc.exists:
        return None
    data = doc.to_dict()
    data["id"] = doc.id
    return data


def query_to_list(query):
    """Convert Firestore query → list of dicts."""
    return [doc_to_dict(d) for d in query.stream()]