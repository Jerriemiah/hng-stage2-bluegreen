## 🧭 Runbook – Blue-Green Deployment with Nginx & Slack Alerting

### 📘 Overview

This runbook documents operational procedures for the **Blue-Green Deployment Monitoring System** used in the `hng-stage2-bluegreen` project.
It explains how to interpret alerts, handle failovers, and respond to high error-rate incidents detected by `watcher.py`, which monitors structured Nginx logs and posts alerts to Slack.

---

### 🧩 System Components

| Component                 | Description                                                                                                                                               |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Nginx (Load Balancer)** | Routes traffic to either Blue or Green app pool based on availability and health.                                                                         |
| **Blue / Green Apps**     | Two identical application containers running on different ports for zero-downtime deployment.                                                             |
| **Watcher**               | A lightweight Python service (`watcher.py`) that tails Nginx access logs, detects failovers or rising error rates, and sends alerts to Slack via webhook. |
| **Slack Channel**         | Receives operational alerts for visibility and quick incident response.                                                                                   |

---

### 🚨 Alert Types

#### 1. **Failover Detected**

**Condition:**
Triggered when the active Nginx upstream pool switches (e.g., from Blue → Green) due to container failure or unavailability.

**Slack Message Example:**

> :rotating_light: *Failover detected!* Pool switched from **blue → green**

**Operator Action:**

1. Verify via logs:

   ```bash
   docker exec -it hng-stage2-bluegreen-nginx-1 tail -n 20 /var/log/nginx/access.log
   ```
2. Check container statuses:

   ```bash
   docker ps
   ```
3. Identify and restart the failed app (usually `app_blue` or `app_green`):

   ```bash
   docker start hng-stage2-bluegreen-app_blue-1
   ```
4. Confirm recovery — Slack will not re-alert unless another pool change occurs (alert deduplicated).

---

#### 2. **High Error Rate**

**Condition:**
Triggered when the percentage of 5xx errors in recent requests exceeds the configured threshold (default: 2%).

**Slack Message Example:**

> :warning: *High error rate detected* — 12.5% of last 200 requests returned errors

**Operator Action:**

1. Inspect Nginx logs for `5xx` responses:

   ```bash
   docker exec -it hng-stage2-bluegreen-nginx-1 tail -n 50 /var/log/nginx/access.log | grep '"status":5'
   ```
2. Check which app pool is serving traffic (pool header):

   ```bash
   curl -s http://localhost:8080/version
   ```
3. Restart or roll back the affected app container if persistent errors occur.
4. The watcher suppresses duplicate alerts for 5 minutes (`ALERT_COOLDOWN_SEC`).

---

### ⚙️ Environment Variables

| Variable               | Description                                             | Example                                |
| ---------------------- | ------------------------------------------------------- | -------------------------------------- |
| `SLACK_WEBHOOK_URL`    | Incoming Slack Webhook URL (secret, set only in `.env`) | `https://hooks.slack.com/services/...` |
| `ERROR_RATE_THRESHOLD` | Error percentage to trigger high error rate alert       | `2`                                    |
| `WINDOW_SIZE`          | Number of recent requests used for rate calculation     | `200`                                  |
| `ALERT_COOLDOWN_SEC`   | Minimum seconds between duplicate alerts                | `300`                                  |
| `LOG_FILE`             | Path to Nginx access log inside watcher container       | `/var/log/nginx/access.log`            |

---

### 🧪 Testing Procedures (Chaos Drill)

| Test                         | Command                                                                                                                                                                                    | Expected Slack Message                                | Screenshot             |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------- | ---------------------- |
| **1. Baseline Test**         | `curl -s http://localhost:8080/version`                                                                                                                                                    | None                                                  | Nginx log JSON line    |
| **2. Failover Simulation**   | `docker stop hng-stage2-bluegreen-app_blue-1`                                                                                                                                              | “Failover detected! Pool switched from blue → green”  | Slack failover alert   |
| **3. Recovery**              | `docker start hng-stage2-bluegreen-app_blue-1`                                                                                                                                             | None                                                  | —                      |
| **4. Error-Rate Simulation** | Stop both apps or one partially: <br> `docker stop hng-stage2-bluegreen-app_green-1 && for i in {1..100}; do curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/version; done` | “High error rate detected — X% of last 200 requests.” | Slack error-rate alert |

---

### 🧹 Recovery Steps Summary

1. **Identify alert** → From Slack channel.
2. **Validate logs** → Check `/var/log/nginx/access.log`.
3. **Inspect containers** → `docker ps`, `docker logs`.
4. **Restart affected container** → `docker start <container>`.
5. **Confirm health** → Run version checks and ensure no further Slack alerts.

---

### ✅ Alert Deduplication

* Watcher only sends a new alert when the pool changes or when error-rate cooldown expires.
* Prevents Slack flooding during prolonged incidents.

---

### 🧾 Notes

* `.env` file should contain the real webhook; `.env.example` must use placeholders only.
* Nginx structured logging must remain single-line JSON for watcher parsing.
* All operational commands should be run from the project root using Docker Compose.

---

### 🏁 End of Runbook

**Maintainer:** `@Jerriemiah`
**Repository:** [https://github.com/Jerriemiah/hng-stage2-bluegreen](https://github.com/Jerriemiah/hng-stage2-bluegreen)
