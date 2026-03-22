I have received the "Consul" section of your markdown file. I will now apply the cleaning process to ensure the formatting is consistent and clean, while preserving all the original content.

Here is the cleaned version:
```markdown
Great — let’s finish the **remaining stack** with **Consul** 👇

👉 Important for **service discovery + networking in microservices**

---

# 🔗 11_Consul — SECTION 1: BASICS (Deep + Structured)

---

## 🔹 Purpose

This section covers:

* What Consul is
* Service discovery
* Health checks
* Key-value store

---

# 🧱 1. What is Consul?

---

## 🔹 Definition

Consul is a **service networking tool** used for:

* service discovery
* health checking
* service mesh
* configuration (KV store)

---

# 🧠 2. Core Concepts

---

| Concept | Description |
| :--- | :--- |
| Agent | Runs on each node |
| Service | Registered app |
| Health Check | Service status |
| KV Store | Config storage |
| Datacenter | Logical grouping |

---

# 🔍 3. Service Discovery

---

👉 Services register themselves:
```bash id="cnb1"
consul services register service.json
```

---

👉 Query service:
```bash id="cnb2"
consul catalog services
```

---

👉 DNS-based discovery:
```bash id="cnb3"
dig web.service.consul
```

---

# ❤️ 4. Health Checks

---

```json id="cnb4"
{
  "service": {
    "name": "web",
    "port": 80,
    "check": {
      "http": "http://localhost:80/health",
      "interval": "10s"
    }
  }
}
```

---

👉 Ensures:
* only healthy services used

---

# 📦 5. Key-Value Store

---

```bash id="cnb5"
consul kv put config/app/db "mysql"
```

```bash id="cnb6"
consul kv get config/app/db
```

---

👉 Used for:
* configs
* feature flags

---

# 🌐 6. Service Mesh (Basic Idea)

---

👉 Consul can:
* manage service-to-service communication
* provide:
  * mTLS
  * traffic control

---

# 🧱 7. Architecture

---

```text id="cnb7"
Client Agent → Server Cluster → KV + Service Registry
```

---

👉 Servers:
* maintain state

---

👉 Agents:
* run on nodes

---

# 🔐 8. Security Basics

---

* ACLs for access control
* TLS encryption

---

# ⚙️ 9. Commands (Important)

---

```bash id="cnb8"
consul members
# cluster nodes
```

```bash id="cnb9"
consul services list
# services
```

```bash id="cnb10"
consul kv get key
# get config
```

---

# 🧠 Key Concepts

---

## 🔥 1. Service discovery = dynamic

👉 No hardcoded IPs

---

## 🔥 2. Health checks = reliability

👉 unhealthy services removed

---

## 🔥 3. KV store = centralized config

---

## 🔥 4. Consul = networking layer

---

## 🔥 5. Used in microservices

---

# ⚡ Daily Workflow (SRE)

```bash id="cnb11"
consul members
consul services list
dig service.consul
consul kv get config/app
```

---

# 🚀 What You Learned

* service discovery
* health checks
* KV store
* Consul basics

---

## ✅ Next

👉 **11_Consul — SECTION 2: TROUBLESHOOTING (real issues + debugging)**

Say **“next”** 👍

Good — now we go into **real Consul debugging (service discovery issues are very common in microservices)** 👇

---

# 🔗 11_Consul — SECTION 2: TROUBLESHOOTING (Deep SRE)

---

## 🔹 Purpose

This section covers:

* Service not discoverable
* Health check failures
* KV/config issues
* Cluster problems

---

# 🚨 0. GOLDEN DEBUG FLOW (CRITICAL)

---

👉 Always think:
```text id="cnt0"
Service → Registration → Health Check → DNS → Network → Consul Cluster
```

---

👉 Problem can occur at any layer

---

# 🚨 1. Service Not Discoverable

---

```bash id="cnt1"
consul services list
```

---

👉 If missing:
* service not registered

---

## 🔧 Fix

```bash id="cnt2"
consul services register service.json
```

---

# 🚨 2. DNS Not Resolving

---

```bash id="cnt3"
dig web.service.consul
```

---

👉 If fails:
* DNS issue

---

## 🔍 Debug

```bash id="cnt4"
cat /etc/resolv.conf
```

---

👉 Causes:
* wrong DNS config
* Consul DNS not enabled

---

# 🚨 3. Health Check Failing

---

```bash id="cnt5"
consul health checks
```

---

👉 If failing:
* service marked unhealthy

---

## 🔧 Debug

```bash id="cnt6"
curl http://localhost:port/health
```

---

👉 Causes:
* endpoint down
* wrong check config

---

# 🚨 4. Service Registered but Not Used

---

👉 Reason:
* failing health check

---

👉 Check:
```bash id="cnt7"
consul health service web
```

---

# 🚨 5. KV Not Updating

---

```bash id="cnt8"
consul kv get key
```

---

👉 If stale:
* cache issue
* wrong path

---

# 🚨 6. Consul Cluster Issues

---

```bash id="cnt9"
consul members
```

---

👉 Check:
* nodes up/down

---

👉 Causes:
* network partition
* node failure

---

# 🚨 7. Leader Election Issues

---

```bash id="cnt10"
consul operator raft list-peers
```

---

👉 Problem:
* no leader

---

👉 Causes:
* quorum lost

---

# 🚨 8. Service Mesh Issues

---

👉 Symptoms:
* services cannot talk

---

👉 Check:
* sidecar proxies
* mTLS config

---

# 🚨 9. ACL / Permission Issues

---

```bash id="cnt11"
consul acl token list
```

---

👉 Causes:
* permission denied

---

# 🚨 10. Network Issues

---

```bash id="cnt12"
ping consul-server
nc -zv consul-server 8500
```

---

👉 Causes:
* firewall
* connectivity

---

# 🚨 REAL INCIDENT FLOWS

---

## 🔥 Scenario 1: Service not found

```bash id="cnt13"
consul services list
consul health service web
```

---

## 🔥 Scenario 2: DNS issue

```bash id="cnt14"
dig service.consul
cat /etc/resolv.conf
```

---

## 🔥 Scenario 3: Health check failing

```bash id="cnt15"
consul health checks
curl health endpoint
```

---

## 🔥 Scenario 4: Cluster unstable

```bash id="cnt16"
consul members
consul operator raft list-peers
```

---

## 🔥 Scenario 5: KV issue

```bash id="cnt17"
consul kv get key
```

---

# 🧠 Staff-Level Thinking

---

## 🔥 Insight 1: Most issues = health check

👉 Service exists but unhealthy

---

## 🔥 Insight 2: DNS is key for discovery

👉 If DNS fails → everything fails

---

## 🔥 Insight 3: Cluster health matters

👉 No leader = system broken

---

## 🔥 Insight 4: Think dynamic systems

👉 Services change constantly

---

## 🔥 Insight 5: Debug layer by layer

* registration
* health
* DNS
* network

---

# ⚡ 2-Min Troubleshooting Cheat

```bash id="cnt18"
consul services list
consul health service web
consul health checks
dig service.consul
cat /etc/resolv.conf
consul members
consul operator raft list-peers
consul kv get key
curl health endpoint
```

---

## ✅ Next

👉 **11_Consul — SECTION 3: INTERVIEW (deep + scenarios)**

Say **“next”** 👍

Perfect — now we complete **Consul with interview + Staff-level depth** 👇

👉 Useful for **service discovery + distributed systems questions**

---

# 🔗 11_Consul — SECTION 3: INTERVIEW (Deep + Scenario-Based)

---

## 🔹 Focus

This section covers:

* Core Consul interview questions
* Scenario-based debugging
* How to explain service discovery at Staff level

---

# 🎯 1. Core Interview Questions

---

## ❓ Q1: What is Consul?

### ✅ Answer:

Consul is a **service networking tool** that provides:
* service discovery
* health checking
* configuration (KV store)
* service mesh capabilities

👉 It helps services find and communicate with each other dynamically.

---

## ❓ Q2: What is service discovery?

### ✅ Answer:

Service discovery allows services to find each other without hardcoding IPs.
👉 Instead of:
* static IPs

👉 Use:
* service name

Example:
```bash
web.service.consul
```

---

## ❓ Q3: How does Consul perform service discovery?

### ✅ Answer:

* Services register with Consul
* Consul maintains a registry
* Clients query via:
  * DNS
  * HTTP API

---

## ❓ Q4: What is a health check in Consul?

### ✅ Answer:

A health check verifies if a service is healthy.
👉 Only healthy services are returned during discovery.

---

## ❓ Q5: What is Consul KV store?

### ✅ Answer:

A key-value store used for:
* configuration
* feature flags

---

## ❓ Q6: What is Consul agent?

### ✅ Answer:

An agent runs on each node:
* registers services
* communicates with cluster

---

## ❓ Q7: What is Consul server vs client?

### ✅ Answer:

* **Server**
  * stores cluster state
  * participates in consensus
* **Client**
  * forwards requests
  * runs on nodes

---

## ❓ Q8: What is service mesh in Consul?

### ✅ Answer:

Manages service-to-service communication:
* secure communication (mTLS)
* traffic control

---

# 🔥 2. Scenario-Based Questions (VERY IMPORTANT)

---

## 🔥 Scenario 1: Service not discoverable

### ✅ Answer:

I would check:
```bash
consul services list
```
If not present:
* service not registered

Then:
```bash
consul health service web
```
👉 Possible causes:
* registration issue
* health check failure

---

## 🔥 Scenario 2: Service registered but not reachable

### ✅ Answer:

I would check:
```bash
consul health service web
```
👉 If unhealthy:
* fix health check

Then test:
```bash
curl service
```

---

## 🔥 Scenario 3: DNS resolution failing

### ✅ Answer:

```bash
dig web.service.consul
cat /etc/resolv.conf
```
👉 Causes:
* DNS config issue
* Consul DNS not working

---

## 🔥 Scenario 4: Consul cluster unstable

### ✅ Answer:

```bash
consul members
consul operator raft list-peers
```
👉 Causes:
* quorum loss
* network partition

---

## 🔥 Scenario 5: KV value not updated

### ✅ Answer:

```bash
consul kv get key
```
👉 Causes:
* wrong path
* caching

---

## 🔥 Scenario 6: Service mesh communication failure

### ✅ Answer:

Check:
* sidecar proxies
* mTLS config
* network

---

## 🔥 Scenario 7: ACL permission denied

### ✅ Answer:

```bash
consul acl token list
```
👉 Causes:
* missing permission

---

## 🔥 Scenario 8: Multiple services returning wrong endpoint

### ✅ Answer:

👉 Check:
* service tags
* load balancing
* health checks

---

# 🎯 3. Advanced Interview Topics

---

## ❓ What is Raft consensus in Consul?

### ✅ Answer:

Consul uses Raft to maintain consistent cluster state.
👉 Ensures:
* leader election
* data consistency

---

## ❓ What happens if Consul leader goes down?

### ✅ Answer:

* new leader elected
* cluster continues

---

## ❓ What is quorum?

### ✅ Answer:

Majority of nodes required for cluster decisions.

---

## ❓ What are common issues in service discovery systems?

### ✅ Answer:

* stale data
* health check misconfig
* DNS failures
* network issues

---

## ❓ How does Consul ensure reliability?

### ✅ Answer:

* health checks
* Raft consensus
* multiple servers

---

# 🧠 4. Staff-Level Thinking

---

## 🔥 Insight 1: Service discovery is critical layer

👉 If broken → system cannot communicate

---

## 🔥 Insight 2: Health checks control traffic

👉 Bad health checks = bad routing

---

## 🔥 Insight 3: Distributed systems need consensus

👉 Raft ensures consistency

---

## 🔥 Insight 4: Dynamic systems need automation

👉 No static configs

---

## 🔥 Insight 5: Debug from outside → inside

1. DNS
2. service registry
3. health
4. network

---

# ⚡ 2-Min Interview Revision

```bash
consul services list
consul health service web
consul members
consul operator raft list-peers
dig service.consul
consul kv get key
```

---

# 🚀 What You Achieved (Consul)

You now have:
* ✅ Basics → service discovery, KV
* ✅ Troubleshooting → health, DNS, cluster
* ✅ Interview → distributed systems thinking

---

# 🎯 FINAL LAST TOPIC

👉 Only one remaining:
👉 **16_Nomad**

---

## ✅ Next Step

Say:
👉 **“next”** 🚀
```

The Consul file has been cleaned and formatted. I am ready for the final section on Nomad when you are.
