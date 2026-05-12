#!/usr/bin/env bash
# Deploy Camelia's booking endpoint + data files to the VPS.
#
# Layout on VPS (Option A — ubuntu owns the files, symlinks expose them):
#   /home/ubuntu/camelia/        <- canonical location, scp target
#       book.php
#       data/
#   /var/www/html/book.php       -> symlink to /home/ubuntu/camelia/book.php
#   /var/www/html/data           -> symlink to /home/ubuntu/camelia/data
#
# First-time setup (run once; uses sudo on VPS, will prompt for password):
#   ./deploy.sh setup
#
# Regular deploy (no sudo):
#   ./deploy.sh
#
# Skip SSH password prompts forever:
#   ssh-copy-id ubuntu@vps-8dd18a9f.vps.ovh.net

set -euo pipefail

HOST="ubuntu@vps-8dd18a9f.vps.ovh.net"
REMOTE_DIR="/home/ubuntu/camelia"
WEB_ROOT="/var/www/html"
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ "${1:-}" == "setup" ]]; then
    echo "First-time setup on $HOST ..."
    ssh "$HOST" "
        mkdir -p $REMOTE_DIR/data/schedules &&
        sudo ln -sfn $REMOTE_DIR/book.php $WEB_ROOT/book.php &&
        sudo ln -sfn $REMOTE_DIR/data    $WEB_ROOT/data
    "
    echo "Setup done. Now run ./deploy.sh to push files."
    exit 0
fi

echo "Deploying to $HOST:$REMOTE_DIR ..."

ssh "$HOST" "mkdir -p $REMOTE_DIR/data/schedules"

scp "$LOCAL_DIR/vps/book.php"             "$HOST:$REMOTE_DIR/book.php"
scp "$LOCAL_DIR/data/leads.json"          "$HOST:$REMOTE_DIR/data/leads.json"
scp "$LOCAL_DIR/data/sales_reps.json"     "$HOST:$REMOTE_DIR/data/sales_reps.json"
scp "$LOCAL_DIR/data/schedules/"*.json    "$HOST:$REMOTE_DIR/data/schedules/"

# Loose perms so the webserver (www-data) can write back updates from book.php.
# Acceptable for the prototype demo; tighten later (ACLs / shared group + setgid).
ssh "$HOST" "chmod -R 777 $REMOTE_DIR/data"

echo
echo "Deployed. Sanity-check:"
echo "  curl -s 'https://prospection.lumelio.fr/book.php?t=baadbeef&s=2026-05-14_morning' | head -20"
