import requests
import os

CONSUL_URL = os.environ.get("CONSUL_HTTP_ADDR", "http://localhost:8500")

def register_service():
    """Registers a 'web' service with Consul."""
    service_payload = {
        "Name": "web",
        "ID": "web-1",
        "Port": 80,
        "Address": "127.0.0.1",
        "Check": {
            "HTTP": "http://example.com", # A simple health check
            "Interval": "10s",
            "Timeout": "1s"
        }
    }
    try:
        response = requests.put(f"{CONSUL_URL}/v1/agent/service/register", json=service_payload)
        response.raise_for_status()
        print("Service 'web' registered successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Error registering service: {e}")

def discover_service():
    """Discovers the 'web' service through Consul."""
    try:
        response = requests.get(f"{CONSUL_URL}/v1/catalog/service/web")
        response.raise_for_status()
        services = response.json()
        if services:
            service = services[0]
            print(f"Discovered 'web' service at {service['ServiceAddress']}:{service['ServicePort']}")
        else:
            print("Service 'web' not found.")
    except requests.exceptions.RequestException as e:
        print(f"Error discovering service: {e}")

if __name__ == "__main__":
    register_service()
    discover_service()
