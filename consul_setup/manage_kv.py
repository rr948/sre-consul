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
