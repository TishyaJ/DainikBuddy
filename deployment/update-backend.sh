#!/bin/bash
# =============================================================================
# Quick Backend Update Script
# Run this ON EC2 when you push new code and want to redeploy
# =============================================================================

set -e

echo "=== Updating PocketBuddy Backend ==="

cd /home/ec2-user/PocketBuddy

# Pull latest code (if using git)
git pull origin main

# Activate venv
source backend/venv/bin/activate

# Install any new dependencies
pip install -r backend/requirements.txt --quiet

# Restart the service
sudo systemctl restart pocketbuddy

echo "Waiting 3s for startup..."
sleep 3

# Check status
sudo systemctl status pocketbuddy --no-pager

echo ""
echo "✓ Backend updated and restarted!"
echo "  Check logs: sudo journalctl -u pocketbuddy -f"
