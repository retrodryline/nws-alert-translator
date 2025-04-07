#!/bin/bash

while true; do
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  echo "📡 [$timestamp] Checking NWS alerts..." | tee -a logs/poller.log
  python -m scheduler.poll_nws 2>&1 | tee -a logs/poller.log
  echo "✅ Done. Sleeping 30 sec..." | tee -a logs/poller.log
  echo "----------------------------------------" | tee -a logs/poller.log
  sleep 30
done
