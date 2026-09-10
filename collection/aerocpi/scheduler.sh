#!/usr/bin/env bash
# AeroCPI daily collection. One cron entry = one observed search_timestamp per day.
# crontab:  30 3 * * *  /home/user/aerocpi/scheduler.sh >> /home/user/aerocpi/collect.log 2>&1
set -euo pipefail
cd "$(dirname "$0")"
ROUTES='[["DEL","BOM",21],["DEL","BLR",21],["BOM","BLR",21],["DEL","MAA",21],
["DEL","CCU",21],["DEL","HYD",21],["BOM","DEL",21],["BLR","DEL",21],
["DEL","BOM",7],["DEL","BOM",14],["DEL","BOM",30],["DEL","BOM",45]]'
python3 collector.py "$(echo "$ROUTES" | tr -d '\n')"
