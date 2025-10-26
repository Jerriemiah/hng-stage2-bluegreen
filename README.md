
# 🚀 HNG Stage 2 DevOps Task — Blue/Green Deployment with Nginx Upstreams

## 🧩 Overview

This project demonstrates a **Blue/Green deployment architecture** using **Docker Compose** and **Nginx** for zero-downtime service updates.

Two identical Node.js containers (`Blue` and `Green`) run simultaneously behind an Nginx reverse proxy.
Nginx directs live traffic to one environment (Blue by default) while keeping the other (Green) idle and ready to take over automatically in case of failure.

---

## 🏗️ Architecture Diagram

```
            +--------------------+
            |     Nginx Router   | ← Exposed on port 8080
            +--------------------+
                  /         \
                 /           \
   +-------------------+   +-------------------+
   |   Blue App (3000) |   |  Green App (3000) |
   |  X-App-Pool: blue |   | X-App-Pool: green |
   +-------------------+   +-------------------+
        localhost:8081         localhost:8082
```

### 🔁 Traffic Flow

* Requests come through **port 8080 (Nginx)**.
* Nginx routes them to the **active pool (Blue)**.
* If the Blue service becomes unavailable or returns errors, Nginx automatically fails over to **Green**, ensuring **no downtime**.

---

## ⚙️ Services Summary

| Service        | Port | Description                                      |
| -------------- | ---- | ------------------------------------------------ |
| `nginx_router` | 8080 | Handles all incoming requests and load balancing |
| `app_blue`     | 8081 | Primary Blue Node.js app container               |
| `app_green`    | 8082 | Secondary Green Node.js app container (backup)   |

---

## 🧾 Environment Variables

All environment variables are defined in a `.env` file (see `.env.example`).

| Variable           | Description                                                     |
| ------------------ | --------------------------------------------------------------- |
| `BLUE_IMAGE`       | Docker image for the Blue app                                   |
| `GREEN_IMAGE`      | Docker image for the Green app                                  |
| `ACTIVE_POOL`      | The currently active deployment environment (`blue` or `green`) |
| `RELEASE_ID_BLUE`  | Version label for Blue                                          |
| `RELEASE_ID_GREEN` | Version label for Green                                         |
| `PORT`             | Internal port the Node.js app runs on (default: 3000)           |

---

## 🛠️ How to Run Locally

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/<your-username>/hng-stage2-bluegreen.git
cd hng-stage2-bluegreen
```

### 2️⃣ Create Your `.env` File

```bash
cp .env.example .env
```

### 3️⃣ Generate Nginx Configuration

```bash
./generate-nginx.sh
```

### 4️⃣ Start All Containers

```bash
docker compose up -d --build
```

### 5️⃣ Verify Setup

```bash
curl -i http://localhost:8080/version
```

Expected output should include:

```
X-App-Pool: blue
X-Release-Id: v1-blue
```

---

## 🧪 Test Automatic Failover

### ✅ Step 1 — Check Current Routing

```bash
for i in {1..5}; do curl -s -i http://localhost:8080/version | grep X-App-Pool; done
```

Expected output:

```
X-App-Pool: blue
```

### ⚠️ Step 2 — Simulate Failure on Blue

```bash
curl -X POST http://localhost:8081/chaos/start?mode=error
```

### 🔄 Step 3 — Observe Failover

```bash
for i in {1..10}; do curl -s -i http://localhost:8080/version | grep X-App-Pool; done
```

Expected output:

```
X-App-Pool: green
```

### 🩺 Step 4 — Restore Blue

```bash
curl -X POST http://localhost:8081/chaos/stop
```

---

## 🧹 Tear Down

To stop and remove all containers, networks, and volumes:

```bash
docker compose down
```

---

## 🧠 Notes

* Images are pulled directly from Docker Hub (`yimikaade/wonderful:devops-stage-two`).
* The app runs on **Node.js (TypeScript)** internally on port `3000`.
* Nginx routes to Blue by default and falls back to Green within seconds if Blue fails.
* The configuration template is dynamically generated using `generate-nginx.sh`.

---

## 👨‍💻 Author Information

**Name:** Jeremiah Inyiama
**Slack Handle:** Jerriemiah
**GitHub:** https://github.com/Jerriemiah/hng-stage2-bluegreen
**Date:** October 2025
