import requests
import json

try:
    response = requests.get('http://localhost:8000/api/admin/meets', timeout=5)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except requests.exceptions.ConnectionError:
    print("ERROR: Cannot connect to backend. Is it running on port 8000?")
except Exception as e:
    print(f"ERROR: {e}")


