Continuing cleanly with **one topic only** 👇

---

# 🔗 11_Consul Command Handbook (Basic + Troubleshooting)

---

# 🔹 PART 1: BASIC COMMANDS (Daily Usage)

---

## 📊 Agent & Cluster Status

```bash id="c1n2m3"
consul members
# List cluster nodes → health + roles (server/client)
```

```bash id="c2n3m4"
consul info
# Detailed agent info → runtime + config
```

```bash id="c3n4m5"
consul operator raft list-peers
# Raft cluster peers → leader + followers
```

---

## 🧭 Services & Catalog

```bash id="c4n5m6"
consul catalog services
# List all registered services
```

```bash id="c5n6m7"
consul catalog nodes
# List nodes in cluster
```

```bash id="c6n7m8"
consul catalog service <service-name>
# Show instances of a service
```

---

## ❤️ Health Checks

```bash id="c7n8m9"
consul health state
# All health checks → passing/warning/critical
```

```bash id="c8n9m1"
consul health checks
# Health check list
```

---

## 🔍 KV Store

```bash id="c9n1m2"
consul kv get config/app
# Read value from KV store
```

```bash id="c10n2m3"
consul kv put config/app value
# Write value to KV store
```

```bash id="c11n3m4"
consul kv list
# List keys
```

---

## 🌐 DNS / Query

```bash id="c12n4m5"
dig @127.0.0.1 -p 8600 service.consul
# Resolve service via Consul DNS
```

---

---

# 🔥 PART 2: TROUBLESHOOTING (SRE CORE)

---

## 🚨 1. Service Not Discoverable

```bash id="t1c2m3"
consul catalog services
# Check if service registered
```

```bash id="t2c3m4"
consul catalog service <service>
# Check instances
```

👉 If missing:

* Service not registered
* Agent issue

---

## 🚨 2. Health Check Failing

```bash id="t3c4m5"
consul health state
# Check failing services
```

```bash id="t4c5m6"
consul health checks
# Detailed check info
```

👉 Root cause:

* App down
* Wrong check config

---

## 🚨 3. Node Not Joining Cluster

```bash id="t5c6m7"
consul members
# Check cluster membership
```

👉 If missing:

* Network issue
* Gossip failure

---

## 🚨 4. Leader Election Issues

```bash id="t6c7m8"
consul operator raft list-peers
# Check leader
```

👉 If no leader:

* Quorum lost
* Network partition

---

## 🚨 5. KV Not Updating

```bash id="t7c8m9"
consul kv get config/app
# Check value
```

👉 Issue:

* Wrong path
* Consistency delay

---

## 🚨 6. DNS Resolution Issues

```bash id="t8c9m1"
dig @127.0.0.1 -p 8600 service.consul
# Test DNS resolution
```

👉 If fails:

* Consul DNS not working
* Service not registered

---

## 🚨 7. Network Issues (Gossip)

```bash id="t9c1m2"
consul members
# Check node status
```

👉 Status:

* alive
* failed
* left

---

## 🚨 8. Debug Logs

```bash id="t10c2m3"
journalctl -u consul
# Consul logs (systemd)
```

```bash id="t11c3m4"
kubectl logs pod/consul
# If running in Kubernetes
```

---

## 🚨 9. ACL / Permission Issues

```bash id="t12c4m5"
consul acl token list
# List tokens
```

```bash id="t13c5m6"
consul acl policy list
# List policies
```

👉 Issue:

* Access denied → ACL misconfig

---

# 🚨 REAL INCIDENT FLOW (Consul)

---

### Scenario: Service not found

```bash id="t14c6m7"
consul catalog services
consul catalog service app
```

---

### Scenario: Service unhealthy

```bash id="t15c7m8"
consul health state
consul health checks
```

---

### Scenario: Cluster issue

```bash id="t16c8m9"
consul members
consul operator raft list-peers
```

---

### Scenario: DNS issue

```bash id="t17c9m1"
dig @127.0.0.1 -p 8600 service.consul
```

---

# 🧠 Staff-Level Thinking

* Consul = **service discovery + health**
* Always check:

  1. Service registered?
  2. Health passing?
  3. Node in cluster?
  4. Leader present?

---

# ⚡ 2-Min Revision

```bash id="t18c1m2"
consul members
consul catalog services
consul catalog service app
consul health state
consul operator raft list-peers
dig @127.0.0.1 -p 8600 service.consul
journalctl -u consul
```

---

## ✅ Next

Next options:

👉 **16_Nomad (scheduler + job failures)**
👉 **18_Ansible (automation debugging)**
👉 **17_SRE Principles (mapped to real incidents)**

Tell me which one 👍
