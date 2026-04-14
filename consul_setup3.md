Of course. This is an excellent next step. You're ready to move from a simple script to a more realistic microservice architecture where an application authenticates itself automatically.

This guide will replace the simple Python script with a **long-running Flask web application**. This application will demonstrate the most important concept you asked for: **Authentication Methods**. It will automatically obtain its own Consul token using a **JWT (JSON Web Token)**, eliminating the need to manually paste a bootstrap token into the code.

### The More Complex Architecture

The core idea is to establish a trust relationship:
1.  We will create a **JWT Auth Method** in Consul. This tells Consul, "I trust JWTs signed with a specific secret key."
2.  We will create a **Binding Rule** that says, "If a service presents a valid JWT with a claim `app_role` set to `api-service`, automatically grant it a Consul token linked to the `api-service-role`."
3.  Our Python Flask application will be "born" with a JWT. On startup, it will perform a "login" to Consul, presenting this JWT.
4.  Consul will validate the JWT, apply the binding rule, and issue a short-lived, less-privileged Consul Token back to the Flask app.
5.  The Flask app will then use **this new, temporary token** for all its operations (like reading from the KV store or discovering other services).

This is exactly how real-world services securely authenticate in an automated way.

---

### Phase 1: Updated Project Files

Your folder structure will now look like this. We are replacing `run_all_examples.py` with two new files: `app.py` (the web service) and `setup_consul.py` (an admin script to configure everything).

```
consul-complex-demo/
├── consul_config/
│   └── acl.json
├── docker-compose.yml
├── Dockerfile
├── app.py              <-- NEW: Our Flask web application
└── setup_consul.py       <-- NEW: Our one-time admin script
```

#### 1. `docker-compose.yml` and `consul_config/acl.json`
These files are perfect and **do not need any changes** from the previous setup. The `healthcheck` is more important than ever here.

#### 2. `Dockerfile` (Updated)
We need to add Flask and a JWT library to our Python image.

```Dockerfile
FROM python:3.9-slim
# Add flask for the web app and pyjwt for handling JSON Web Tokens
RUN pip install requests flask PyJWT
WORKDIR /app
# Copy both of our new Python scripts
COPY *.py /app/
```

#### 3. `setup_consul.py` (The Admin Script)
This script replaces the old "run-all" script. Its job is to be run **once** by you (the administrator) to configure everything in Consul. It creates the necessary policies, roles, and the JWT Auth Method.

```python
# setup_consul.py
import requests
import json
import time
import jwt

# --- CONFIGURATION ---
CONSUL_URL = "http://localhost:8500"  # We run this from our local machine
# This is the master token you get from the 'acl bootstrap' command
CONSUL_TOKEN = "YOUR_BOOTSTRAP_TOKEN_HERE"
# This is a secret key used to sign the JWT. In production, this would be a secure, shared secret.
JWT_SECRET_KEY = "my-super-secret-key-for-signing-jwts"
# --------------------

HEADERS = {"X-Consul-Token": CONSUL_TOKEN, "Content-Type": "application/json"}

def setup_all():
    print("--- 1. Creating KV Store Entry ---")
    kv_headers = {"X-Consul-Token": CONSUL_TOKEN}
    requests.put(f"{CONSUL_URL}/v1/kv/config/api-service/message", data="Hello from the KV Store!", headers=kv_headers).raise_for_status()
    print("✅ KV entry created.")

    print("\n--- 2. Creating ACL Policy and Role for our Service ---")
    # This policy grants the permissions our Flask app will need
    policy_name = "api-service-policy"
    policy_rules = """
    # Allow reading the KV store under its own config path
    key_prefix "config/api-service/" {
      policy = "read"
    }
    # Allow registering itself as a service
    service_prefix "api-service" {
      policy = "write"
    }
    # Allow discovering any service
    service_prefix "" {
        policy = "read"
    }
    """
    policy_payload = {"Name": policy_name, "Rules": policy_rules}
    requests.put(f"{CONSUL_URL}/v1/acl/policy", data=json.dumps(policy_payload), headers=HEADERS).raise_for_status()
    print(f"✅ Created Policy: '{policy_name}'")

    # This role links the policy
    role_name = "api-service-role"
    role_payload = {"Name": role_name, "Policies": [{"Name": policy_name}]}
    requests.put(f"{CONSUL_URL}/v1/acl/role", data=json.dumps(role_payload), headers=HEADERS).raise_for_status()
    print(f"✅ Created Role: '{role_name}'")

    print("\n--- 3. Creating JWT Authentication Method ---")
    auth_method_payload = {
        "Name": "my-jwt-provider",
        "Type": "jwt",
        "Config": {
            "JWTValidationPubKeys": [JWT_SECRET_KEY],
            "BoundAudiences": ["consul-demo-app"],
            "ClaimMappings": {
                "app_role": "app_role"
            }
        }
    }
    requests.put(f"{CONSUL_URL}/v1/acl/auth-method/my-jwt-provider", data=json.dumps(auth_method_payload), headers=HEADERS).raise_for_status()
    print("✅ Created JWT Auth Method.")

    # This is the crucial link!
    binding_rule_payload = {
        "Description": "Binds JWT app_role to Consul Role",
        "Selector": "'api-service' in app_role",
        "BindType": "role",
        "BindName": role_name
    }
    requests.put(f"{CONSUL_URL}/v1/acl/binding-rule", data=json.dumps(binding_rule_payload), headers=HEADERS).raise_for_status()
    print("✅ Created Binding Rule: JWTs with 'api-service' role will get the right Consul role.")

    print("\n--- 4. Generating a JWT for our Application ---")
    # In the real world, an identity provider would issue this. Here, we generate it ourselves.
    app_jwt = jwt.encode(
        {
            "aud": "consul-demo-app",
            "exp": int(time.time()) + 3600, # Expires in 1 hour
            "app_role": ["api-service"] # The custom claim our binding rule looks for
        },
        JWT_SECRET_KEY,
        algorithm="HS256"
    )
    print("✅ Generated JWT for the application. The app will use this to log in.")
    print("\n--- JWT for app.py ---")
    print(app_jwt)
    print("--- End of JWT ---\n")
    
    print("\n🎉 Setup complete! You can now run the Flask application.")

if __name__ == "__main__":
    if CONSUL_TOKEN == "YOUR_BOOTSTRAP_TOKEN_HERE":
        print("❌ FATAL: Please paste your bootstrap token into the 'CONSUL_TOKEN' variable before running.")
    else:
        setup_all()

```

#### 4. `app.py` (The Complex Application)
This is the Flask web service. It does **not** contain the bootstrap token. Instead, it holds the JWT and uses it to log in and get its own working token.

```python
# app.py
from flask import Flask, jsonify
import requests
import os
import time

app = Flask(__name__)

# --- CONFIGURATION ---
CONSUL_AGENT_URL = os.environ.get("CONSUL_HTTP_ADDR")
SERVICE_NAME = "api-service"
SERVICE_PORT = 5000

# This is the JWT generated by the setup_consul.py script.
# PASTE THE GENERATED JWT HERE!
APP_JWT = "YOUR_APP_JWT_HERE"

# This will hold the short-lived Consul token after we log in.
consul_token = None
# --------------------

def login_to_consul():
    """Performs a login to Consul using the JWT to get a Consul ACL token."""
    global consul_token
    print("--- Attempting to log in to Consul using JWT... ---")
    try:
        login_payload = {
            "AuthMethod": "my-jwt-provider",
            "BearerToken": APP_JWT
        }
        response = requests.post(f"{CONSUL_AGENT_URL}/v1/acl/login", json=login_payload)
        response.raise_for_status()
        consul_token = response.json()["SecretID"]
        print("✅ Successfully logged in to Consul. Received a temporary ACL token.")
        return True
    except Exception as e:
        print(f"❌ FATAL: Could not log in to Consul: {e}")
        return False

def register_service_with_consul():
    """Registers this service with the local Consul agent."""
    if not consul_token:
        print("Cannot register service, no Consul token.")
        return

    print(f"--- Registering '{SERVICE_NAME}' with Consul... ---")
    service_payload = {
        "Name": SERVICE_NAME,
        "Port": SERVICE_PORT,
        "Check": {
            "HTTP": f"http://localhost:{SERVICE_PORT}/health",
            "Interval": "10s"
        }
    }
    headers = {"X-Consul-Token": consul_token}
    try:
        requests.put(f"{CONSUL_AGENT_URL}/v1/agent/service/register", json=service_payload, headers=headers).raise_for_status()
        print("✅ Service registered successfully.")
    except Exception as e:
        print(f"❌ Could not register service: {e}")

@app.route("/health")
def health():
    return "OK", 200

@app.route("/")
def index():
    return jsonify({"message": "Welcome to the complex API service!"})

@app.route("/config")
def get_config():
    """Reads a configuration value from the Consul KV store."""
    if not consul_token:
        return "Error: Not logged into Consul", 500
    
    headers = {"X-Consul-Token": consul_token}
    try:
        response = requests.get(f"{CONSUL_AGENT_URL}/v1/kv/config/api-service/message", headers=headers)
        response.raise_for_status()
        # The value is Base64 encoded in the JSON response
        import base64
        message = base64.b64decode(response.json()[0]['Value']).decode('utf-8')
        return jsonify({"message_from_kv": message})
    except Exception as e:
        return f"Error reading from KV store: {e}", 500

if __name__ == "__main__":
    # The application startup sequence:
    # 1. Log in to Consul to get a token.
    # 2. Register itself with Consul.
    # 3. Start the web server.
    if APP_JWT == "YOUR_APP_JWT_HERE":
        print("❌ FATAL: Please paste the application JWT into the 'APP_JWT' variable in app.py")
    elif login_to_consul():
        time.sleep(1) # Small delay before registering
        register_service_with_consul()
        app.run(host="0.0.0.0", port=SERVICE_PORT)

```

---

### Phase 2: The New Step-by-Step Workflow

This workflow has two main parts: a one-time admin setup, and then running the application.

#### **Part A: One-Time Administrative Setup**

**Step 1: Destroy and Start the Cluster**
Start from a perfectly clean slate.

```bash
docker-compose down -v
docker-compose up --build -d
```

**Step 2: Get the Bootstrap Token**
Generate the master key for the new cluster.

```bash
docker exec consul-server-1 consul acl bootstrap
```
**Copy the `SecretID` from the output.**

**Step 3: Configure Consul using the Admin Script**
1.  Open the `setup_consul.py` file.
2.  Paste the `SecretID` you just copied into the `CONSUL_TOKEN` variable.
3.  Save the file.
4.  **Run the script from your local machine**, not inside a container. It's an admin task. Make sure you have the required Python libraries installed locally (`pip install requests pyjwt`).
    ```bash
    python setup_consul.py
    ```

**Step 4: Copy the Application JWT**
The `setup_consul.py` script will print out a long JWT string. **Copy this entire JWT string.**

```
--- JWT for app.py ---
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJjb25zdWwtZGVtby1hcHAiLCJleHAiOjE2N...
--- End of JWT ---
```

#### **Part B: Run the Complex Application**

**Step 5: Give the Application its JWT**
1.  Open the `app.py` file.
2.  Paste the JWT you just copied into the `APP_JWT` variable.
3.  Save the file.

**Step 6: Rebuild and Restart the App Container**
You've changed the `app.py` script, so you must rebuild the image and restart the container to apply the change.

```bash
docker-compose build --no-cache python-app
docker-compose up -d --force-recreate python-app
```

**Step 7: Verify Everything is Running**
Your Flask application is now running inside the `python-app` container. Check its logs to see the successful login and registration messages.

```bash
docker logs python-app
```
You should see:
```
--- Attempting to log in to Consul using JWT... ---
✅ Successfully logged in to Consul. Received a temporary ACL token.
--- Registering 'api-service' with Consul... ---
✅ Service registered successfully.
 * Serving Flask app 'app'
 * Running on http://0.0.0.0:5000
...
```

**Step 8: Interact with Your Complex Application**
*   **Check the UI:** Go to `http://localhost:8500`, log in with your bootstrap token, and look at the `app-node-1` node. You will now see the `api-service` registered, and its health check will be green!
*   **Call the API:** You can now interact with your running Flask app. Find its IP address in the Docker network.
    ```bash
    # Get the IP of your app container
    docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' python-app

    # Now use that IP to call its /config endpoint
    curl http://<IP_ADDRESS_OF_PYTHON_APP>:5000/config
    ```
    You should get a JSON response with the message from the KV store, proving that your app successfully authenticated, got a token, and used it to read from Consul.
