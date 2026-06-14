# Step-by-Step AWS Deployment for Amazon HackOn

Total time: ~2 hours. All free tier.

---

## PHASE 1: AWS Account Setup (5 min)

### What YOU do:

1. Go to https://aws.amazon.com → Create account (if you don't have one)
2. Install AWS CLI on your Windows machine:
   ```
   winget install Amazon.AWSCLI
   ```
3. Configure CLI:
   ```
   aws configure
   ```
   Enter: Access Key, Secret Key, Region: `ap-south-1` (Mumbai), Output: `json`

> **Where to get keys:** AWS Console → IAM → Users → Your user → Security Credentials → Create Access Key

---

## PHASE 2: Deploy Backend on EC2 (45 min)

### Step 2.1: Launch EC2 Instance

**What YOU do in AWS Console (https://console.aws.amazon.com/ec2/):**

1. Click **Launch Instance**
2. Settings:
   - Name: `PocketBuddy-Backend`
   - AMI: **Amazon Linux 2023** (free tier eligible)
   - Instance type: **t3.micro** (free tier — 750 hrs/mo for 12 months)
   - Key pair: Create new → name it `pocketbuddy-key` → Download `.pem` file
   - Network: Allow SSH (22), HTTP (80), HTTPS (443), Custom TCP (8000)
     - Under "Security group" → "Edit" → Add rules:
       - Type: HTTP, Source: Anywhere
       - Type: Custom TCP, Port: 8000, Source: Anywhere
3. Click **Launch Instance**
4. Wait ~1 minute for it to start

### Step 2.2: Note your public IP

Go to EC2 → Instances → Click your instance → Copy the **Public IPv4 address**
(something like `13.233.xx.xx`)

### Step 2.3: SSH into the instance

**What YOU do in your terminal (PowerShell):**

```powershell
# Key is in project .ssh folder
# SSH in (replace IP with yours)
ssh -i "d:\HACKON\PocketBuddy\.ssh\pocketbuddy-key.pem" ec2-user@YOUR_EC2_PUBLIC_IP
```

### Step 2.4: Run setup on EC2

**What YOU do INSIDE the EC2 SSH session:**

Option A — If repo is on GitHub:
```bash
# Install git and clone
sudo dnf install -y git python3.11 python3.11-pip nginx
git clone https://github.com/YOUR_USERNAME/PocketBuddy.git
cd PocketBuddy
bash deployment/ec2-setup.sh
```

Option B — If repo is NOT on GitHub (manual upload):
```bash
# On your LOCAL machine, upload the backend folder:
scp -i ~/.ssh/pocketbuddy-key.pem -r backend/ ec2-user@YOUR_IP:/home/ec2-user/PocketBuddy/backend/
scp -i ~/.ssh/pocketbuddy-key.pem -r deployment/ ec2-user@YOUR_IP:/home/ec2-user/PocketBuddy/deployment/

# Then SSH in and run setup manually:
ssh -i ~/.ssh/pocketbuddy-key.pem ec2-user@YOUR_IP
cd /home/ec2-user/PocketBuddy
bash deployment/ec2-setup.sh
```

### Step 2.5: Configure .env

**What YOU do (still in SSH):**

```bash
nano /home/ec2-user/PocketBuddy/backend/.env
```

Paste your actual values (copy from your local `backend/.env`). 
**Critical:** Update `CORS_ORIGINS` to include your frontend URL (we'll get it in Phase 3).

Save: `Ctrl+O`, `Enter`, `Ctrl+X`

### Step 2.6: Start the backend

```bash
sudo systemctl start pocketbuddy
sudo systemctl status pocketbuddy
```

You should see: `Active: active (running)`

### Step 2.7: Test it

```bash
curl http://localhost:8000/docs
```

Should return HTML (Swagger UI). From your LOCAL browser, try:
```
http://YOUR_EC2_PUBLIC_IP/docs
```

If you see the API docs page, **backend is live!** 🎉

---

## PHASE 3: Deploy Frontend on S3 (30 min)

### Step 3.1: Update frontend .env

**What YOU do locally:**

Edit `frontend/.env`:
```
REACT_APP_BACKEND_URL=http://YOUR_EC2_PUBLIC_IP
```

### Step 3.2: Build the frontend

```powershell
cd frontend
npm run build
```

### Step 3.3: Create S3 bucket and upload

**What YOU do:**

```powershell
# Create bucket (use a unique name — bucket names are global)
aws s3api create-bucket --bucket pocketbuddy-demo-YOUR_TEAM_NAME --region ap-south-1 --create-bucket-configuration LocationConstraint=ap-south-1

# Disable block public access
aws s3api put-public-access-block --bucket pocketbuddy-demo-YOUR_TEAM_NAME --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

# Set bucket policy for public read
aws s3api put-bucket-policy --bucket pocketbuddy-demo-YOUR_TEAM_NAME --policy "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"PublicRead\",\"Effect\":\"Allow\",\"Principal\":\"*\",\"Action\":\"s3:GetObject\",\"Resource\":\"arn:aws:s3:::pocketbuddy-demo-YOUR_TEAM_NAME/*\"}]}"

# Enable static website hosting
aws s3 website s3://pocketbuddy-demo-YOUR_TEAM_NAME/ --index-document index.html --error-document index.html

# Upload build
aws s3 sync frontend/build/ s3://pocketbuddy-demo-YOUR_TEAM_NAME/ --delete
```

### Step 3.4: Get your live URL

Your frontend is now live at:
```
http://pocketbuddy-demo-YOUR_TEAM_NAME.s3-website.ap-south-1.amazonaws.com
```

Open that in your browser. If you see the PocketBuddy app, **frontend is live!** 🎉

---

## PHASE 4: Connect Frontend ↔ Backend (10 min)

### Step 4.1: Update CORS on backend

SSH back into EC2:
```bash
ssh -i ~/.ssh/pocketbuddy-key.pem ec2-user@YOUR_EC2_PUBLIC_IP
nano /home/ec2-user/PocketBuddy/backend/.env
```

Update `CORS_ORIGINS` to include your S3 URL:
```
CORS_ORIGINS=http://pocketbuddy-demo-YOUR_TEAM_NAME.s3-website.ap-south-1.amazonaws.com,http://localhost:3000
```

Restart backend:
```bash
sudo systemctl restart pocketbuddy
```

### Step 4.2: Verify end-to-end

Open your S3 URL in browser → Try to register/login → If it works, you're done!

---

## PHASE 5 (Optional): Add CloudFront for HTTPS (15 min)

For a more polished demo with `https://` URL:

1. AWS Console → CloudFront → Create Distribution
2. Origin domain: `pocketbuddy-demo-YOUR_TEAM_NAME.s3-website.ap-south-1.amazonaws.com`
   - **Important:** Use the S3 website endpoint URL, NOT the S3 bucket URL
3. Protocol: HTTP only (for origin)
4. Viewer protocol: Redirect HTTP to HTTPS
5. Default root object: `index.html`
6. Custom error pages: 403 → /index.html (200) — needed for React Router
7. Create distribution

Wait 5–10 min for deployment. You get: `https://d1234abcdef.cloudfront.net`

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't SSH into EC2 | Check Security Group has port 22 open; check key file permissions |
| Backend won't start | Check `.env` values: `sudo journalctl -u pocketbuddy -n 50` |
| Frontend shows blank | Check browser console for CORS errors; update CORS_ORIGINS |
| Chat hangs/timeouts | Nginx SSE config issue — ensure `proxy_buffering off` is set |
| MongoDB connection fails | Whitelist EC2 IP in MongoDB Atlas (Network Access → Add IP) |
| S3 403 Forbidden | Check bucket policy allows public read; check block public access is OFF |

---

## Architecture Diagram for Demo Slides

```
┌──────────────┐         ┌──────────────────────┐
│   Browser    │ ──────▶ │  S3 + CloudFront     │
│  (React PWA) │         │  (Static Frontend)   │
└──────┬───────┘         └──────────────────────┘
       │ API calls
       ▼
┌──────────────────────┐
│  EC2 t3.micro        │
│  Nginx → Uvicorn     │
│  FastAPI (Python)     │
│  AI Engine (4 LLMs)   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  MongoDB Atlas M0    │
│  (Cloud Database)    │
└──────────────────────┘
```

All on AWS Free Tier. Zero cost for demo.
