# Blue/Green Deployment with NGINX, Docker Compose & Observability

**DevOps Learning Project | Zero-Downtime Deployment | Failover | Monitoring & Alerts**

---

## Overview

This project demonstrates a **Blue/Green deployment architecture** implemented using **Docker Compose** and **NGINX upstreams**, extended with **real-time observability and Slack alerts**.

Two identical application instances (Blue and Green) run in parallel behind an NGINX reverse proxy. Traffic is routed to the active environment (Blue by default), while the standby environment (Green) remains available for **instant failover**. If the active service fails, NGINX automatically retries the request against the backup within the **same client request**, ensuring **zero downtime**.

The setup was completed as part of the **HNG DevOps Internship (Stage 2 & Stage 3)** and focuses on **deployment reliability, fault tolerance, and operational visibility**.

---

## Project Objectives

This project was designed to demonstrate the ability to:

* Implement Blue/Green deployment without Kubernetes
* Configure NGINX upstream failover and retry behavior
* Achieve zero failed client requests during service failure
* Parameterize deployments using environment variables
* Monitor runtime behavior through structured logs
* Detect failovers and error spikes via automated alerts
* Document operational response via a runbook

---

## High-Level Architecture

```
Client
  |
  v
+--------------------+
|   NGINX Router     |  :8080
+--------------------+
        |
        | (Upstream routing)
        |
  -------------------------
  |                       |
+-------------------+   +-------------------+
|  Blue App (3000)  |   | Green App (3000)  |
|  :8081            |   | :8082             |
|  Primary          |   | Backup            |
+-------------------+   +-------------------+
```

---

## Traffic & Failover Behavior

* **Normal state:**
  All traffic is routed to **Blue**

* **Failure state:**
  If Blue returns a timeout or 5xx error:

  * NGINX retries the request against Green
  * The client still receives a **200 OK**
  * Traffic continues on Green until recovery

* **Headers forwarded unchanged:**

  * `X-App-Pool: blue | green`
  * `X-Release-Id: <release-id>`

---

## Services Summary

| Service       | Port | Purpose                       |
| ------------- | ---- | ----------------------------- |
| nginx_router  | 8080 | Entry point & traffic routing |
| app_blue      | 8081 | Primary application instance  |
| app_green     | 8082 | Backup application instance   |
| alert_watcher | —    | Log monitoring & Slack alerts |

---

## Environment Configuration

All configuration is driven via environment variables.

Defined in `.env.example`:

| Variable               | Description                               |
| ---------------------- | ----------------------------------------- |
| `BLUE_IMAGE`           | Docker image for Blue app                 |
| `GREEN_IMAGE`          | Docker image for Green app                |
| `ACTIVE_POOL`          | Initial active pool (blue or green)       |
| `RELEASE_ID_BLUE`      | Release label for Blue                    |
| `RELEASE_ID_GREEN`     | Release label for Green                   |
| `PORT`                 | Internal application port (default: 3000) |
| `SLACK_WEBHOOK_URL`    | Slack incoming webhook                    |
| `ERROR_RATE_THRESHOLD` | % of 5xx errors to trigger alert          |
| `WINDOW_SIZE`          | Sliding window size for error tracking    |
| `ALERT_COOLDOWN_SEC`   | Alert rate-limit duration                 |

---

## Deployment Flow

1. Docker Compose starts all services
2. `generate-nginx.sh` builds NGINX config from template
3. NGINX routes traffic based on `ACTIVE_POOL`
4. Applications expose health, chaos, and version endpoints
5. NGINX logs enriched request metadata
6. Log watcher parses logs in real time
7. Slack alerts fire on failover or error spikes

---

## Running the Project Locally

### 1. Clone Repository

```bash
git clone https://github.com/Jerriemiah/hng-stage2-bluegreen.git
cd hng-stage2-bluegreen
```

### 2. Create Environment File

```bash
cp .env.example .env
```

### 3. Generate NGINX Configuration

```bash
./generate-nginx.sh
```

### 4. Start Services

```bash
docker compose up -d --build
```

---

## Verification Steps

### Check Active Pool

```bash
curl -i http://localhost:8080/version
```

Expected headers:

```
X-App-Pool: blue
X-Release-Id: <blue-release>
```

---

## Chaos & Failover Testing

### Simulate Failure on Blue

```bash
curl -X POST http://localhost:8081/chaos/start?mode=error
```

### Observe Automatic Failover

```bash
for i in {1..10}; do
  curl -s -i http://localhost:8080/version | grep X-App-Pool
done
```

Expected:

```
X-App-Pool: green
```

### Restore Blue

```bash
curl -X POST http://localhost:8081/chaos/stop
```

---

## Observability & Monitoring (Stage 3 Extension)

### Structured NGINX Logs

NGINX access logs were extended to include:

* Active pool
* Release ID
* Upstream address
* Upstream status
* Request & upstream latency

Logs are written to a **shared volume** for consumption by the watcher service.

---

### Log Watcher Service

A lightweight Python service (`watcher.py`) monitors NGINX logs in real time and:

* Detects pool changes (Blue ↔ Green)
* Tracks upstream 5xx error rates
* Maintains a rolling request window
* Applies alert cooldowns to prevent spam

---

### Slack Alerts

Alerts are sent to Slack when:

* **Failover occurs**
* **Error rate exceeds threshold**

Alerts include:

* Timestamp
* Pool transition
* Error context

---

## Runbook

Operational response steps are documented in `runbook.md`, including:

* Failover alert handling
* Error-rate investigation
* Recovery validation
* Maintenance mode considerations

---

## Repository Structure

```text
.
├── docker-compose.yml
├── nginx.conf.template
├── nginx.conf
├── generate-nginx.sh
├── watcher.py
├── watcher.Dockerfile
├── requirements.txt
├── runbook.md
├── .env.example
├── logs/nginx/
└── README.md
```

---

## Key Learnings

* Designing zero-downtime deployments without orchestration platforms
* Implementing NGINX upstream failover and retries
* Using logs as a source of truth for observability
* Detecting incidents without direct application instrumentation
* Building alerting systems with rate limiting and context
* Writing operator-friendly runbooks

---

## Limitations & Future Improvements

* Manual pool switching could be extended with health-based auto-recovery
* TLS termination could be added
* Metrics could be exported to Prometheus
* CI-based chaos testing could be automated

---

## Why This Project Matters

This project demonstrates **real DevOps thinking**:

* Reliability over convenience
* Observability over guesswork
* Automation without over-engineering
* Clear operational documentation

It complements IT Support experience by showing **infrastructure reliability, failure handling, and production-style operations**.

---

## Author

**Jeremiah Inyiama**
GitHub: [https://github.com/Jerriemiah](https://github.com/Jerriemiah)
Slack: Jerriemiah

---


