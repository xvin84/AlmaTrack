import requests

try:
    res = requests.get("http://localhost:5000/dashboard")
    print("STATUS:", res.status_code)
    print("TEXT:", res.text[:500])
except Exception as e:
    print(e)
