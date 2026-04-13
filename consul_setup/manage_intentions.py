import requests
import os

CONSUL_URL = os.environ.get("CONSUL_HTTP_ADDR", "http://localhost:8500")

def setup_intentions():
    """Sets up service intentions for a service mesh."""
    # 1. Set the default policy to 'deny'
    print("Setting default policy to deny...")
    deny_all_payload = {"Name": "*", "Action": "deny"}
    requests.post(f"{CONSUL_URL}/v1/connect/intentions", json=deny_all_payload).raise_for_status()

    # 2. Create an explicit 'allow' intention
    print("Allowing 'dashboard' to connect to 'database'...")
    allow_payload = {
        "SourceName": "dashboard",
        "DestinationName": "database",
        "Action": "allow"
    }
    response = requests.post(f"{CONSUL_URL}/v1/connect/intentions", json=allow_payload)
    response.raise_for_status()
    print("Intention created successfully.")
    print(response.json())

if __name__ == "__main__":
    setup_intentions()
