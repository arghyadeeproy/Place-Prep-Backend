import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api"

# 🔐 Firebase credentials for testing
FIREBASE_WEB_API_KEY = "AIzaSyBphgrsa7a5IJqPkKHdhwOUPSv1WV4tAUU"
TEST_EMAIL = "test@test1.com"
TEST_PASSWORD = "test123"


# ─────────────────────────────────────────────
# FIREBASE LOGIN (Auto Token Fetch)
# ─────────────────────────────────────────────

def get_firebase_token():
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"

    r = requests.post(url, json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "returnSecureToken": True
    })

    if r.status_code != 200:
        print("❌ Firebase Login Failed")
        print(r.text)
        sys.exit(1)

    return r.json()["idToken"]


# ─────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────

def log(title):
    print(f"\n{'='*70}")
    print(f"🔹 {title}")
    print('='*70)


def show(res):
    print("STATUS:", res.status_code)
    try:
        print(json.dumps(res.json(), indent=2))
    except:
        print(res.text)


def check(res):
    if res.status_code >= 400:
        print("❌ FAILED")
        sys.exit(1)
    print("✅ PASSED")


# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────

def test_profile(headers):
    log("AUTH → PROFILE")
    r = requests.get(f"{BASE_URL}/auth/profile/", headers=headers)
    show(r)
    check(r)


# ─────────────────────────────────────────────
# PLACEMENT
# ─────────────────────────────────────────────

def test_popular(headers):
    log("PLACEMENT → POPULAR")
    r = requests.get(f"{BASE_URL}/placement/popular/", headers=headers)
    show(r)
    check(r)


def test_company(headers):
    log("PLACEMENT → COMPANY GUIDE")
    r = requests.get(f"{BASE_URL}/placement/company/google/", headers=headers)
    show(r)
    check(r)


# ─────────────────────────────────────────────
# SKILLTEST
# ─────────────────────────────────────────────

def test_topics(headers):
    log("SKILLTEST → TOPICS")
    r = requests.get(f"{BASE_URL}/skilltest/topics/", headers=headers)
    show(r)
    check(r)


def test_generate(headers):
    log("SKILLTEST → GENERATE")
    r = requests.post(
        f"{BASE_URL}/skilltest/generate/",
        headers=headers,
        json={
            "topic": "DSA",
            "difficulty": "Medium",
            "count": 5
        }
    )
    show(r)
    check(r)
    return r.json()["data"]["session_id"]


def test_submit(headers, session_id):
    log("SKILLTEST → SUBMIT")
    r = requests.post(
        f"{BASE_URL}/skilltest/submit/{session_id}/",
        headers=headers,
        json={
            "answers": {
                "0": 1,
                "1": 2,
                "2": 0,
                "3": 3,
                "4": 1
            },
            "time_taken_seconds": 120,
            "tab_switches": 0
        }
    )
    show(r)
    check(r)


def test_attempts(headers):
    log("SKILLTEST → ATTEMPTS")
    r = requests.get(f"{BASE_URL}/skilltest/attempts/", headers=headers)
    show(r)
    check(r)


def test_leaderboard(headers):
    log("SKILLTEST → LEADERBOARD")
    r = requests.get(f"{BASE_URL}/skilltest/leaderboard/", headers=headers)
    show(r)
    check(r)


# ─────────────────────────────────────────────
# DEV2DEV
# ─────────────────────────────────────────────

def test_create_post(headers):
    log("DEV2DEV → CREATE POST")
    r = requests.post(
        f"{BASE_URL}/dev2dev/posts/",
        headers=headers,
        json={
            "title": "Automated Test Post",
            "body": f"Created at {datetime.now()}",
            "tags": ["DSA"]
        }
    )
    show(r)
    check(r)
    return r.json()["data"]["id"]


# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────

def test_dashboard(headers):
    log("DASHBOARD")
    r = requests.get(f"{BASE_URL}/dashboard/", headers=headers)
    show(r)
    check(r)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":

    print("\n🚀 STARTING FULL API TEST SUITE")

    print("\n🔐 Logging into Firebase...")
    id_token = get_firebase_token()

    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }

    test_profile(headers)

    test_popular(headers)
    test_company(headers)

    test_topics(headers)
    session_id = test_generate(headers)
    test_submit(headers, session_id)
    test_attempts(headers)
    test_leaderboard(headers)

    test_create_post(headers)

    test_dashboard(headers)

    print("\n🎉 ALL ROUTES WORKING SUCCESSFULLY")