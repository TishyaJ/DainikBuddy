#!/bin/bash
# =============================================================================
# EC2 Instance Setup Script
# Run this AFTER SSH-ing into your new EC2 t2.micro instance
# OS: Amazon Linux 2023 (recommended) or Ubuntu 22.04
# =============================================================================

set -e

echo "=== PocketBuddy EC2 Setup ==="

# --- Step 1: System updates ---
echo "[1/7] Updating system packages..."
sudo dnf update -y

# --- Step 2: Install Python 3.11 ---
echo "[2/7] Installing Python 3.11..."
sudo dnf install -y python3.11 python3.11-pip python3.11-devel git nginx

# --- Step 3: Clone the repo ---
echo "[3/7] Cloning PocketBuddy..."
cd /home/ec2-user
git clone https://github.com/YOUR_USERNAME/PocketBuddy.git
cd PocketBuddy/backend

# --- Step 4: Create venv and install deps ---
echo "[4/7] Setting up Python environment..."
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# --- Step 5: Create .env file ---
echo "[5/7] Creating .env file..."
cat > .env << 'EOF'
# === PASTE YOUR VALUES HERE ===
MONGO_URL=mongodb+srv://YOUR_USER:YOUR_PASS@cluster.mongodb.net/?appName=pocketbuddy&tls=true&tlsAllowInvalidCertificates=true
DB_NAME=pocketbuddy
JWT_SECRET=YOUR_JWT_SECRET_HERE_AT_LEAST_32_CHARS
CORS_ORIGINS=https://YOUR_CLOUDFRONT_URL.cloudfront.net,http://localhost:3000

# === AI KEYS ===
EMERGENT_LLM_KEY=your-key
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AI...
GROQ_API_KEY=gsk_...
EOF

echo ""
echo "⚠️  IMPORTANT: Edit /home/ec2-user/PocketBuddy/backend/.env with your real values!"
echo "    Use: nano /home/ec2-user/PocketBuddy/backend/.env"
echo ""

# --- Step 6: Install systemd service ---
echo "[6/7] Installing systemd service..."
sudo cp /home/ec2-user/PocketBuddy/deployment/pocketbuddy.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pocketbuddy

# --- Step 7: Install nginx config ---
echo "[7/7] Configuring nginx..."
sudo cp /home/ec2-user/PocketBuddy/deployment/nginx.conf /etc/nginx/conf.d/pocketbuddy.conf

# Remove default nginx page
sudo rm -f /etc/nginx/conf.d/default.conf 2>/dev/null || true

sudo systemctl enable nginx
sudo systemctl restart nginx

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Next steps:"
echo "  1. Edit .env:  nano /home/ec2-user/PocketBuddy/backend/.env"
echo "  2. Start app:  sudo systemctl start pocketbuddy"
echo "  3. Check logs:  sudo journalctl -u pocketbuddy -f"
echo "  4. Test:        curl http://localhost:8000/docs"
echo ""
