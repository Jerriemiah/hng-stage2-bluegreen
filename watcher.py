import os
import time
import json
import requests
from collections import deque
import sys

# --- Configuration ---
LOG_FILE = "/var/log/nginx/access.log"
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
ERROR_RATE_THRESHOLD = float(os.getenv("ERROR_RATE_THRESHOLD", 2))  # %
WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", 200))
ALERT_COOLDOWN_SEC = int(os.getenv("ALERT_COOLDOWN_SEC", 300))

# --- State ---
last_pool = None
last_alert_time = 0
recent_statuses = deque(maxlen=WINDOW_SIZE)


def log(msg):
    """Print with immediate flush."""
    print(msg, flush=True)


def post_to_slack(message):
    if not SLACK_WEBHOOK_URL:
        log("[WARN] SLACK_WEBHOOK_URL not set, skipping alert.")
        return

    try:
        response = requests.post(SLACK_WEBHOOK_URL, json={"text": message}, timeout=10)
        if response.status_code != 200:
            log(f"[WARN] Slack responded with {response.status_code}: {response.text}")
        else:
            log("[Watcher] ✅ Slack alert sent successfully.")
    except Exception as e:
        log(f"[ERROR] Failed to send Slack alert: {e}")


def check_failover(pool):
    global last_pool
    if last_pool and pool != last_pool:
        msg = f":rotating_light: Failover detected! Pool switched from *{last_pool}* → *{pool}*"
        log(msg)
        post_to_slack(msg)
    last_pool = pool


def check_error_rate():
    if not recent_statuses:
        return
    errors = sum(1 for s in recent_statuses if s.startswith("5"))
    rate = (errors / len(recent_statuses)) * 100
    if rate > ERROR_RATE_THRESHOLD:
        global last_alert_time
        now = time.time()
        if now - last_alert_time > ALERT_COOLDOWN_SEC:
            msg = f":warning: High error rate detected — {rate:.2f}% of last {len(recent_statuses)} requests."
            log(msg)
            post_to_slack(msg)
            last_alert_time = now


def tail_log():
    log(f"[Watcher] Monitoring {LOG_FILE} ...")

    while not os.path.exists(LOG_FILE):
        log("[Watcher] Waiting for log file to appear...")
        time.sleep(2)

    with open(LOG_FILE, "r") as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue

            line = line.strip()
            if not line:
                continue

            # Each access log JSON block spans multiple lines
            if not line.startswith("{"):
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                log("[Watcher] Skipped malformed JSON line.")
                continue

            pool = data.get("pool", "unknown")
            status = str(data.get("status", "0"))

            check_failover(pool)
            recent_statuses.append(status)
            check_error_rate()


if __name__ == "__main__":
    log("[Watcher] Starting log watcher...")
    log(f"[Watcher] SLACK_WEBHOOK_URL set: {'yes' if SLACK_WEBHOOK_URL else 'no'}")
    tail_log()
