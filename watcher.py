import os
import time
import json
import requests
from collections import deque

# Environment variables
LOG_FILE = "/var/log/nginx/access.log"
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
ERROR_RATE_THRESHOLD = float(os.getenv("ERROR_RATE_THRESHOLD", 2))  # percent
WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", 200))
ALERT_COOLDOWN_SEC = int(os.getenv("ALERT_COOLDOWN_SEC", 300))

last_pool = None
last_alert_time = 0
recent_statuses = deque(maxlen=WINDOW_SIZE)

def post_to_slack(message):
    if not SLACK_WEBHOOK_URL:
        print("[WARN] SLACK_WEBHOOK_URL not set, skipping alert.")
        return
    try:
        requests.post(SLACK_WEBHOOK_URL, json={"text": message})
    except Exception as e:
        print(f"[ERROR] Failed to send Slack alert: {e}")

def check_failover(pool):
    global last_pool
    if last_pool and pool != last_pool:
        post_to_slack(f":rotating_light: Failover detected! Pool switched from {last_pool} → {pool}")
    last_pool = pool

def check_error_rate():
    if not recent_statuses:
        return
    errors = sum(1 for s in recent_statuses if s.startswith("5"))
    rate = (errors / len(recent_statuses)) * 100
    if rate > ERROR_RATE_THRESHOLD:
        now = time.time()
        global last_alert_time
        if now - last_alert_time > ALERT_COOLDOWN_SEC:
            post_to_slack(f":warning: High error rate detected — {rate:.2f}% of last {len(recent_statuses)} requests.")
            last_alert_time = now

def tail_log():
    with open(LOG_FILE, "r") as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue
            try:
                data = json.loads(line.strip())
                pool = data.get("pool", "unknown")
                status = str(data.get("status", "0"))
                check_failover(pool)
                recent_statuses.append(status)
                check_error_rate()
            except json.JSONDecodeError:
                continue

if __name__ == "__main__":
    print("[Watcher] Starting log watcher...")
    tail_log()
