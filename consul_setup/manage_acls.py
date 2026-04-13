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
