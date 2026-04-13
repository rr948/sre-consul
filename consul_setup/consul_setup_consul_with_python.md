Of course. Here is the complete, documented guide for the final, working setup. You can save this as a `README.md` file in your project folder. It contains everything you need to replicate this environment, including prerequisites, architecture explanations, all file contents, and a definitive step-by-step workflow.

---

# Complete Guide: Secure, Multi-Node Consul Cluster with Python & Docker

This document provides a full, reusable guide for setting up and interacting with a secure, highly-available HashiCorp Consul cluster. The entire environment is containerized using Docker Compose.

## 1. Architecture Overview

This setup creates a realistic, containerized Consul environment with the following components:

*   **Consul Server Cluster (3 Nodes):** A three-node server cluster (`consul-server-1`, `-2`, `-3`) provides high availability and fault tolerance. They use the Raft algorithm to elect a leader and replicate data.
*   **Consul Client Agent (1 Node):** A single, non-server agent (`consul-client-1`) runs as a "sidecar." This is the standard pattern where your application doesn't need to know the server addresses; it only communicates with its local agent.
*   **Python Application (1 Container):** A simple Python container (`python-app`) that runs our demonstration script. It is configured to communicate exclusively with its sidecar `consul-client-1` agent.
*   **Secure by Default:** The cluster has Access Control Lists (ACLs) enabled with a `"default_policy": "deny"`. All interactions (from the API or the UI) require a valid token to succeed.

### Communication Flow

```
+-------------------------------------------------------------------------+
| Your Local Machine (Docker Host)                                        |
|                                                                         |
|  Browser -> http://localhost:8500 -> [consul-server-1 UI]               |
|                                                                         |
|  +-------------------------------------------------------------------+  |
|  | Docker Network                                                    |  |
|  |                                                                   |  |
|  |  +----------------+      +-------------------+      +-----------+  |  |
|  |  | consul-server-1| <--> | consul-server-2   | <--> | consul-se |  |  |
|  |  +----------------+      +-------------------+      +-----------+  |  |
|  |          ^                      (Raft Peering)                    |  |
|  |          | (API Forwarding)                                       |  |
|  |  +----------------+      +----------------+                      |  |
|  |  | consul-client-1| <--- |   python-app   |                      |  |
|  |  +----------------+      +----------------+                      |  |
|  |    (Sidecar Agent)         (Demo Script)                         |  |
|  |                                                                   |  |
|  +-------------------------------------------------------------------+  |
|                                                                         |
+-------------------------------------------------------------------------+
```

## 2. Prerequisites

You only need two tools installed on your machine:

1.  **Docker:** To run the containers.
2.  **Docker Compose:** To orchestrate the multi-container environment defined in the `docker-compose.yml` file.

## 3. Project Files

Create a new directory for your project and place the following files inside it.

#### `docker-compose.yml`
This is the master file that defines our entire architecture. It includes a critical **healthcheck** to ensure the cluster is stable before the Python application is allowed to start, preventing race conditions.

```yaml
services:
  # --- CONSUL SERVER CLUSTER (3 NODES) ---
  consul-server-1:
    image: hashicorp/consul:1.15
    container_name: consul-server-1
    ports:
      - "8500:8500" # Expose UI/API to your local machine from this server
      - "8600:8600/udp"
    volumes:
      - ./consul_config:/consul/config
    command: "agent -server -bootstrap-expect=3 -ui -node=consul-server-1 -client=0.0.0.0"

  consul-server-2:
    image: hashicorp/consul:1.15
    container_name: consul-server-2
    volumes:
      - ./consul_config:/consul/config
    command: "agent -server -node=consul-server-2 -retry-join=consul-server-1"

  consul-server-3:
    image: hashicorp/consul:1.15
    container_name: consul-server-3
    volumes:
      - ./consul_config:/consul/config
    command: "agent -server -node=consul-server-3 -retry-join=consul-server-1"

  # --- APPLICATION NODE WITH CONSUL CLIENT (SIDECAR) ---
  consul-client-1:
    image: hashicorp/consul:1.15
    container_name: consul-client-1
    volumes:
      - ./consul_config:/consul/config
    # CRITICAL: -client=0.0.0.0 allows the python-app container to connect to this agent
    command: "agent -node=app-node-1 -retry-join=consul-server-1 -client=0.0.0.0"
    depends_on:
      - consul-server-1
    # CRITICAL HEALTHCHECK: Ensures the cluster has a leader before other services start.
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8500/v1/status/leader"]
      interval: 5s
      timeout: 1s
      retries: 10

  python-app:
    build: .
    container_name: python-app
    environment:
      - CONSUL_HTTP_ADDR=http://consul-client-1:8500
    # CRITICAL: This ensures python-app only starts after consul-client-1 is fully healthy and connected to a leader.
    depends_on:
      consul-client-1:
        condition: service_healthy
    command: tail -f /dev/null
```

#### `Dockerfile`
This file defines how to build our simple Python application container.

```Dockerfile
FROM python:3.9-slim
# Install libraries for making HTTP requests
RUN pip install requests
WORKDIR /app
# Copy our single, all-in-one script into the container
COPY run_all_examples.py /app/
```

#### `consul_config/acl.json`
This configuration file is mounted into all Consul containers and tells them to enable the ACL system on startup.

```json
{
  "acl": {
    "enabled": true,
    "default_policy": "deny",
    "enable_token_persistence": true
  }
}
```

#### `run_all_examples.py`
This is the final, fully-working Python script that demonstrates all features.

<details>
<summary>Click to see the full Python code</summary>

```python
import requests
import json
import os
import time

# --- CONFIGURATION ---
# The address of the local sidecar agent, provided by docker-compose
CONSUL_URL = os.environ.get("CONSUL_HTTP_ADDR")
# This is the master token you will get from the 'acl bootstrap' command.
# PASTE YOUR TOKEN HERE!
CONSUL_TOKEN = "YOUR_BOOTSTRAP_TOKEN_HERE"
# --------------------

# This header will be used for all standard API requests
HEADERS = {"X-Consul-Token": CONSUL_TOKEN, "Content-Type": "application/json"}


def demo_peers():
    print("\n--- 1. DEMO: PEERS ---")
    try:
        response = requests.get(f"{CONSUL_URL}/v1/status/peers", headers=HEADERS)
        response.raise_for_status()
        peers = response.json()
        print(f"✅ Successfully queried Raft peers. Found {len(peers)} peers (servers).")
        for peer in peers:
            print(f"  - Peer: {peer}")
    except Exception as e:
        print(f"❌ Error getting peers: {e}")

def demo_nodes_and_services():
    print("\n--- 2. DEMO: NODES & SERVICES ---")
    try:
        service_payload = {"Name": "api-service", "ID": "api-1", "Port": 8080, "tags": ["production", "api"]}
        requests.put(f"{CONSUL_URL}/v1/agent/service/register", data=json.dumps(service_payload), headers=HEADERS).raise_for_status()
        print("✅ Successfully registered 'api-service' on the local agent ('app-node-1').")
        print("➡️  VERIFY: In the UI, go to Nodes -> app-node-1 to see this service.")
    except Exception as e:
        print(f"❌ Error registering service: {e}")

def demo_kv():
    print("\n--- 3. DEMO: KEY/VALUE (KV) STORE ---")
    try:
        kv_payload = "db.my-company.internal"
        # For KV, the payload is raw data, not JSON, so we remove the Content-Type header for this call.
        kv_headers = {"X-Consul-Token": CONSUL_TOKEN}
        requests.put(f"{CONSUL_URL}/v1/kv/config/database/hostname", data=kv_payload, headers=kv_headers).raise_for_status()
        print("✅ Successfully wrote value to 'config/database/hostname'.")
        print("➡️  VERIFY: In the UI, go to the Key/Value tab.")
    except Exception as e:
        print(f"❌ Error with KV store: {e}")

def demo_intentions():
    print("\n--- 4. DEMO: INTENTIONS (SERVICE MESH) ---")
    try:
        # Add a more robust delay to ensure the service has propagated to the servers before creating an intention.
        print("   (Waiting 5 seconds for service mesh to initialize...)")
        time.sleep(5)
        intention_payload = {"SourceName": "dashboard-app", "DestinationName": "api-service", "Action": "allow"}
        requests.post(f"{CONSUL_URL}/v1/connect/intentions", data=json.dumps(intention_payload), headers=HEADERS).raise_for_status()
        print("✅ Successfully created intention: 'dashboard-app' is now allowed to connect to 'api-service'.")
        print("➡️  VERIFY: In the UI, go to the Intentions tab.")
    except Exception as e:
        print(f"❌ Error creating intention: {e}")

def demo_full_acl_workflow():
    print("\n--- 5. DEMO: FULL ACL WORKFLOW (POLICIES, ROLES, TOKENS) ---")
    try:
        # A. Create a read-only ACL Policy using the correct Consul API endpoint
        policy_name = "kv-readonly-policy"
        policy_payload = {
            "Name": policy_name,
            "Rules": 'key_prefix "config/" { policy = "read" }'
        }
        requests.put(f"{CONSUL_URL}/v1/acl/policy", data=json.dumps(policy_payload), headers=HEADERS).raise_for_status()
        print(f"✅ Successfully created ACL Policy: '{policy_name}'")

        # B. Create an ACL Role that uses the policy
        role_name = "database-config-reader"
        role_payload = {
            "Name": role_name,
            "Policies": [{"Name": policy_name}]
        }
        requests.put(f"{CONSUL_URL}/v1/acl/role", data=json.dumps(role_payload), headers=HEADERS).raise_for_status()
        print(f"✅ Successfully created ACL Role: '{role_name}'")

        # C. Create a new, temporary Token from that role
        token_payload = {
            "Description": "Temporary token for the reader app",
            "Roles": [{"Name": role_name}]
        }
        response = requests.put(f"{CONSUL_URL}/v1/acl/token", data=json.dumps(token_payload), headers=HEADERS)
        response.raise_for_status()
        new_token_secret_id = response.json()['SecretID']
        print(f"✅ Successfully created a new, less-privileged token from the role.")
        print(f"  - New Token SecretID (first 8 chars): {new_token_secret_id[:8]}...")
        print("➡️  VERIFY: In the UI, go to the ACL tab to see the new Policy, Role, and Token.")

        # D. Test the new token's permissions
        print("--- Testing new token's permissions... ---")
        test_headers = {"X-Consul-Token": new_token_secret_id}
        # This read should succeed
        requests.get(f"{CONSUL_URL}/v1/kv/config/database/hostname", headers=test_headers).raise_for_status()
        print("  - ✅ Read Test: PASSED. New token can read from 'config/'.")
        # This write should fail
        try:
            write_response = requests.put(f"{CONSUL_URL}/v1/kv/config/newkey", data="test", headers=test_headers)
            if write_response.status_code == 403:
                print("  - ✅ Write Test: PASSED. New token was correctly denied (403 Forbidden).")
            else:
                 print(f"  - ❌ Write Test: FAILED. Expected 403, but got {write_response.status_code}.")
        except Exception as e:
             print(f"  - ❌ Write Test: FAILED with exception {e}.")

    except Exception as e:
        print(f"❌ Error during ACL workflow: {e}")


if __name__ == "__main__":
    if CONSUL_TOKEN == "YOUR_BOOTSTRAP_TOKEN_HERE":
        print("❌ FATAL: Please paste your bootstrap token into the 'CONSUL_TOKEN' variable in the script before running.")
    else:
        print("🚀 Starting Consul Demo In 3 Seconds...")
        time.sleep(3)
        demo_peers()
        demo_nodes_and_services()
        demo_kv()
        demo_intentions()
        demo_full_acl_workflow()
        print("\n🎉 Demo complete!")
```
</details>

## 4. Step-by-Step Execution Workflow

Follow these steps exactly to run the demonstration.

#### Step 1: Destroy Any Old Environment (The "Reset Button")
This is the most important step for a repeatable demo. It stops all containers and **deletes all old Consul data**, ensuring you start from a perfectly clean slate.

```bash
docker-compose down -v
```

#### Step 2: Start the New Cluster
This command builds your Python image and starts all 5 containers. It will take a moment longer than before because `docker-compose` now waits for the `healthcheck` to confirm the cluster has a leader before starting the `python-app`.

```bash
docker-compose up --build -d
```

#### Step 3: Generate the Master Security Token
Run this command to bootstrap the new cluster's ACL system. This will create and print the one-and-only master key (Bootstrap Token).

```bash
docker exec consul-server-1 consul acl bootstrap
```

#### Step 4: Copy the `SecretID`
From the output of the previous command, find and copy the `SecretID` value. This is your master token.

```
AccessorID:       b2c8a2e2-3c35-4f4c-8f2e-3c354f4c8f2e
SecretID:         a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6   <-- COPY THIS VALUE
Description:      Bootstrap Token (Global Management)
...
```

#### Step 5: Update the Python Script
Open the `run_all_examples.py` file. Find the line `CONSUL_TOKEN = "YOUR_BOOTSTRAP_TOKEN_HERE"` and paste the `SecretID` you just copied. Save the file.

#### Step 6: Rebuild the Python App with the New Token
You've changed the script, so you must rebuild the image to include that change.

```bash
docker-compose build --no-cache python-app
```

#### Step 7: Restart the Python App Container
This command forces `docker-compose` to restart your app, ensuring it uses the newly built image containing the correct token.

```bash
docker-compose up -d --force-recreate python-app
```

#### Step 8: Log In to the Consul UI
1.  Go to `http://localhost:8500` in your browser.
2.  Click **"Log in"** in the top-right corner.
3.  Paste the same **`SecretID`** (your bootstrap token) into the box and log in.
4.  You can now explore the UI and see your 4 healthy nodes (3 servers, 1 client).

#### Step 9: Run the Demonstration Script
Execute the main script. It will run all the demonstrations sequentially.

```bash
docker exec python-app python run_all_examples.py
```

#### Step 10: Verify the Results
After the script finishes successfully, **refresh your browser window** showing the Consul UI. Now, go through the UI tabs to see all the items your script created:
*   **Nodes:** Click on `app-node-1` to see the `api-service`.
*   **Key/Value:** See the `config/database/hostname` key.
*   **Intentions:** See the `dashboard-app` -> `api-service` rule.
*   **ACL:** Click on **Policies**, **Roles**, and **Tokens** to see the new `kv-readonly-policy`, `database-config-reader` role, and the temporary `temp-app-token`.

You have now successfully set up, secured, and interacted with a complete Consul cluster.
