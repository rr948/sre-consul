Of course. Here is a comprehensive set of examples that demonstrates how to use Consul's core features—Nodes, Services, KV Store, Intentions, and ACL Tokens—with Python and Docker.

This guide uses the `hvac` library, which is primarily for HashiCorp Vault but has excellent capabilities for interacting with Consul, especially when dealing with ACLs. We will also use `requests` for direct API calls to keep the examples clear.

### Project Setup

First, let's define a `docker-compose.yml` file to run a Consul agent in development mode with the UI enabled. This setup makes it easy to experiment with the API.

**`docker-compose.yml`:**
```yaml
version: "3.8"
services:
  consul-server:
    image: hashicorp/consul:1.15
    container_name: consul-server
    ports:
      - "8500:8500" # Consul API & UI
      - "8600:8600/udp" # Consul DNS
    volumes:
      - ./consul_config:/consul/config
    command: "agent -server -bootstrap-expect=1 -ui -client=0.0.0.0 -enable-script-checks=true"

  python-app:
    build: .
    container_name: python-app
    depends_on:
      - consul-server
    environment:
      - CONSUL_HTTP_ADDR=http://consul-server:8500
    command: tail -f /dev/null # Keep the container running
```

You will also need a simple `Dockerfile` for the Python application.

**`Dockerfile`:**
```Dockerfile
FROM python:3.9-slim
RUN pip install hvac requests
WORKDIR /app
```

### 1. Nodes and Services

Nodes are the machines running a Consul agent. Services are applications running on those nodes. You can register a service to make it discoverable.

This example registers a "web" service with a health check.

**`register_service.py`:**
```python
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
```

### 2. Key/Value (KV) Store

The KV store is a flexible data store for dynamic configuration, feature flags, and coordination.

**`manage_kv.py`:**
```python
import hvac
import os

client = hvac.Client(url=os.environ.get("CONSUL_HTTP_ADDR", "http://localhost:8500"))

def write_kv():
    """Writes a key-value pair to the Consul KV store."""
    print("Writing key 'app/config/db_host'...")
    client.secrets.kv.v1.create_or_update_secret(
        mount_point='kv',
        path='app/config/db_host',
        secret=dict(value='db.example.com'),
    )
    print("Key written successfully.")

def read_kv():
    """Reads a key-value pair from the Consul KV store."""
    print("Reading key 'app/config/db_host'...")
    response = client.secrets.kv.v1.read_secret(
        mount_point='kv',
        path='app/config/db_host',
    )
    db_host = response['data']['value']
    print(f"Read value: {db_host}")

if __name__ == "__main__":
    write_kv()
    read_kv()
```

### 3. Intentions (Service Mesh)

Intentions define which services are allowed to communicate with each other in a Consul service mesh. This is the foundation of zero-trust networking.

This example creates an intention that allows a "dashboard" service to talk to a "database" service but denies all other traffic by default.

**`manage_intentions.py`:**
```python
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
```

### 4. ACL Tokens (Security)

ACLs (Access Control Lists) secure the Consul API, UI, and service communications. You create policies that define permissions and then generate tokens associated with those policies.

This example defines a read-only policy for the KV store and creates a token for it.

First, enable ACLs by creating `consul_config/acl.json`:
```json
{
  "acl": {
    "enabled": true,
    "default_policy": "deny",
    "enable_token_persistence": true
  }
}
```

**`manage_acls.py`:**
```python
import hvac
import os

# Use the bootstrap token to create policies and other tokens
# In a real setup, this would be a securely stored secret.
BOOTSTRAP_TOKEN = "YOUR_BOOTSTRAP_TOKEN" # Get this from Consul logs on first start

client = hvac.Client(
    url=os.environ.get("CONSUL_HTTP_ADDR", "http://localhost:8500"),
    token=BOOTSTRAP_TOKEN,
)

def create_acl_policy_and_token():
    """Creates a read-only policy for the KV store and a token for it."""
    policy_name = "kv-reader"
    policy_rules = """
    # Grant read-only access to all keys in the KV store
    key_prefix "" {
      policy = "read"
    }
    """

    print(f"Creating ACL policy '{policy_name}'...")
    client.sys.create_or_update_acl_policy(name=policy_name, rules=policy_rules)
    print("Policy created.")

    print(f"Creating a token for the '{policy_name}' policy...")
    token_response = client.auth.token.create(policies=[policy_name], lease="1h")
    read_only_token = token_response['auth']['client_token']

    print(f"Read-only token created: {read_only_token}")
    print("\n--- Testing the new token ---")
    test_token(read_only_token)

def test_token(token):
    """Uses the new token to try and read/write from the KV store."""
    reader_client = hvac.Client(url=os.environ.get("CONSUL_HTTP_ADDR"), token=token)

    # 1. Try to read (should succeed)
    try:
        response = reader_client.secrets.kv.v1.read_secret(mount_point='kv', path='app/config/db_host')
        print(f"SUCCESS (Read): Got value: {response['data']['value']}")
    except Exception as e:
        print(f"ERROR (Read): {e}")

    # 2. Try to write (should fail)
    try:
        reader_client.secrets.kv.v1.create_or_update_secret(
            mount_point='kv', path='app/config/new_key', secret=dict(value='test')
        )
        print("ERROR (Write): Write operation succeeded but should have failed.")
    except Exception as e:
        print(f"SUCCESS (Write): Write operation failed as expected. Error: {e}")

if __name__ == "__main__":
    # IMPORTANT: You need to get the bootstrap token from the Consul server logs
    # the first time you start it with ACLs enabled.
    if BOOTSTRAP_TOKEN == "YOUR_BOOTSTRAP_TOKEN":
        print("Please replace 'YOUR_BOOTSTRAP_TOKEN' with the actual bootstrap token from Consul's logs.")
    else:
        create_acl_policy_and_token()
```


Of course. Here is a step-by-step guide on how to set up your environment and run the Python examples to interact with HashiCorp Consul.

### Prerequisites

*   You must have **Docker** and **Docker Compose** installed on your machine.

---

### Step 1: Create Your Project Directory and Files

First, create a folder for your project and then create all the files from the previous example inside it.

Your final project structure should look like this:

```
consul-python-demo/
├── consul_config/
│   └── acl.json
├── docker-compose.yml
├── Dockerfile
├── register_service.py
├── manage_kv.py
├── manage_intentions.py
└── manage_acls.py
```

1.  Create the main directory:
    ```bash
    mkdir consul-python-demo
    cd consul-python-demo
    ```

2.  Create the Python files (`register_service.py`, `manage_kv.py`, `manage_intentions.py`, `manage_acls.py`) and the `Dockerfile` and `docker-compose.yml` exactly as provided in the previous response.

---

### Step 2: Start the Consul Environment

Now, let's start the Consul server and the Python application container.

1.  Build the Docker image and start the containers in detached mode:
    ```bash
    docker-compose up --build -d
    ```

2.  **Verify Consul is running**: Open your web browser and navigate to **`http://localhost:8500`**. You should see the Consul UI.

---

### Step 3: Run the Examples

You will execute each Python script inside the `python-app` container using the `docker exec` command.

#### Example A: Nodes & Services

1.  Run the script to register a service:
    ```bash
    docker exec python-app python register_service.py
    ```
    You will see the output confirming the service was registered and discovered.

2.  **Check the Consul UI**:
    *   Go to `http://localhost:8500`.
    *   Click on the **Services** tab in the left-hand menu. You will see the **`web`** service listed, likely with a red "critical" status because the health check to `example.com` is just for demonstration.
    *   Click on the **Nodes** tab. You will see the default `consul-server` node.

#### Example B: Key/Value Store

1.  Run the script to write and read a KV pair:
    ```bash
    docker exec python-app python manage_kv.py
    ```

2.  **Check the Consul UI**:
    *   Navigate to the **Key/Value** tab.
    *   You will see the key `app/config/db_host` with the value `db.example.com`.

#### Example C: Intentions

1.  Run the script to create service intentions:
    ```bash
    docker exec python-app python manage_intentions.py
    ```

2.  **Check the Consul UI**:
    *   Navigate to the **Intentions** tab.
    *   You will see two rules: one `* -> * (deny)` and one `dashboard -> database (allow)`. This demonstrates a "deny by default" security posture.

---

### Step 4: Run the ACLs Example (Requires Restart)

This example is more involved because it requires enabling ACLs in Consul, which must be done on startup.

1.  **Stop and Remove the Containers**:
    ```bash
    docker-compose down
    ```

2.  **Create the ACL Configuration File**:
    *   Create a directory named `consul_config`.
    *   Inside it, create a file named `acl.json` with the following content:
        ```json
        {
          "acl": {
            "enabled": true,
            "default_policy": "deny",
            "enable_token_persistence": true
          }
        }
        ```

3.  **Restart Consul and Get the Bootstrap Token**:
    *   Start the containers again, but this time **in the foreground** so you can see the logs:
        ```bash
        docker-compose up --build
        ```
    *   In the logs from the `consul-server` container, find the **Bootstrap Token**. It will look like this (your `SecretID` will be different):
        ```
        consul-server    | ==> Consul agent running!
        ...
        consul-server    |     Bootstrap Token: 8f6f5e34-5f0a-4b3e-8b3e-1b3e8f6f5e34
        ...
        ```
    *   Copy the `SecretID` (the UUID string).

4.  **Update the ACL Script**:
    *   Open your `manage_acls.py` file.
    *   Replace the placeholder `"YOUR_BOOTSTRAP_TOKEN"` with the token you just copied.

5.  **Execute the ACL Script**:
    *   You can leave the `docker-compose up` command running. Open a **new terminal window** and navigate to your project directory.
    *   Run the script:
        ```bash
        docker exec python-app python manage_acls.py
        ```
    *   The output will show the script creating the policy and token, and then successfully reading from the KV store while failing to write, as expected.

6.  **Check the Consul UI**:
    *   Go to `http://localhost:8500`. You will now be prompted for a token. Use the **Bootstrap Token** to log in.
    *   Navigate to the **ACL** tab. Under **Policies**, you will see your `kv-reader` policy. Under **Tokens**, you will see the new token created by the script.

---

### Step 5: Clean Up Your Environment

Once you are finished, you can stop and remove all the containers and networks.

```bash
docker-compose down
```
