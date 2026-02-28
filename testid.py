import requests

API_KEY = "AIzaSyBphgrsa7a5IJqPkKHdhwOUPSv1WV4tAUU"

res = requests.post(
    f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}",
    json={
        "email": "test@test1.com",
        "password": "test123",
        "returnSecureToken": True
    }
)

print(res.json()["idToken"])