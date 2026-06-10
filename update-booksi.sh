#!/bin/bash
# update-booksi.sh — run by cron to keep booksi data fresh
set -e

cd /home/woodmastr/code/fg/booksi

# Log file
LOG=./data/update.log
echo "=== $(date) ===" >> "$LOG"

# Step 1: scrape new data (HTML only, no images)
echo "  scraping..." >> "$LOG"
./getGals.sh >> "$LOG" 2>&1

# Step 2: extract tar.gz if needed, process with booksi.py
echo "  extracting..." >> "$LOG"
for tar in ./data/*.tar.gz; do
    dir="${tar%.tar.gz}"
    dirname=$(basename "$dir")
    if [ ! -d "./data/$dirname" ]; then
        tar -zxf "$tar" -C ./data/
    fi
done

# Step 3: process data
echo "  processing..." >> "$LOG"
uv run python booksi.py >> "$LOG" 2>&1

# Step 4: copy all.html to web root
echo "  deploying..." >> "$LOG"
cp all.html /var/www/booksi/all.html

echo "  done" >> "$LOG"
