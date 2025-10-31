#!/bin/bash
# Temporarily break one app (Blue)
docker exec hng-stage2-bluegreen-app_blue-1 pkill node

# Send requests to generate error responses
for i in {1..50}; do curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/version; done

# Watch watcher output
docker logs -f alert_watcher
