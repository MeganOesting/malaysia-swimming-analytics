import requests
import json

try:
    # Test the meets endpoint
    response = requests.get('http://localhost:8000/api/meets')
    print(f"Status code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except requests.exceptions.ConnectionError:
    print("❌ Could not connect to backend. Is it running on http://localhost:8000?")
except Exception as e:
    print(f"❌ Error: {e}")


