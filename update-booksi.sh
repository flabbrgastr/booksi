#!/bin/bash
# update-booksi.sh — run by cron to keep booksi data fresh
set -e

PATH="/usr/local/bin:/usr/bin:/bin:/home/woodmastr/.local/bin"
export PATH

cd /home/woodmastr/code/fg/booksi

LOG=./data/update.log
echo "=== $(date) ===" >> "$LOG"

# Step 1: scrape new data, keep folder (-f) so booksi.py can read it
echo "  scraping..." >> "$LOG"
uv run python pyGals.py -f >> "$LOG" 2>&1

# Step 2: extract any tar.gz that doesn't have a directory yet
# (fallback in case getGals.sh wasn't run with -f)
for tar in ./data/*.tar.gz; do
    [ -f "$tar" ] || continue
    dirname=$(basename "$tar" .tar.gz)
    if [ ! -d "./data/$dirname" ]; then
        echo "  extracting $dirname..." >> "$LOG"
        tar -zxf "$tar" -C ./data/
    fi
done

# Step 3: process data
echo "  processing..." >> "$LOG"
uv run python booksi.py >> "$LOG" 2>&1

# Step 4: deploy to web root
echo "  deploying..." >> "$LOG"
cp all.html /var/www/booksi/all.html

echo "  done" >> "$LOG"
