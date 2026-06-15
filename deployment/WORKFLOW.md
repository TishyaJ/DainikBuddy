# Deployment Workflow — What to Do After Code Changes

## Live URLs

| What | URL |
|------|-----|
| Frontend (App) | http://pocketbuddy-frontend-demo.s3-website-ap-southeast-2.amazonaws.com |
| Backend (API) | http://54.206.59.45 |
| API Docs (Swagger) | http://54.206.59.45/docs |

## SSH Key Location

```
d:\HACKON\PocketBuddy\.ssh\pocketbuddy-key.pem
```

---

## Quick Reference

| Changed | What to do |
|---------|-----------|
| Frontend files (`.jsx`, `.css`, `.js`) | Build locally → Upload to S3 |
| Backend files (`.py`) | SCP upload → Restart service on EC2 |
| Backend `.env` | Edit on EC2 directly → Restart |
| Both frontend + backend | Do both steps |

---

## Scenario 1: Frontend Changes Only

**Where:** Run in your LOCAL PowerShell (Windows)

```powershell
# 1. Build the frontend
cd d:\HACKON\PocketBuddy\frontend
npm run build

# 2. Upload to S3
$env:AWS_ACCESS_KEY_ID = $env:MY_AWS_KEY        # from deployment/.env
$env:AWS_SECRET_ACCESS_KEY = $env:MY_AWS_SECRET  # from deployment/.env
$env:AWS_DEFAULT_REGION = "ap-southeast-2"
& "D:\HACKON\aws.exe" s3 sync build/ s3://pocketbuddy-frontend-demo/ --delete

# NOTE: Get actual key values from deployment/.env (not committed to git)

```

Done. Changes are live in ~10 seconds.

---

## Scenario 2: Backend Changes (SCP Upload — No GitHub Needed)

**Step 1:** Upload changed files from LOCAL PowerShell:
```powershell
# Upload a single file (e.g., server.py)
scp -i "d:\HACKON\PocketBuddy\.ssh\pocketbuddy-key.pem" backend/server.py ec2-user@54.206.59.45:/home/ec2-user/DainikBuddy/backend/

# Upload entire backend folder
scp -i "d:\HACKON\PocketBuddy\.ssh\pocketbuddy-key.pem" -r backend/ ec2-user@54.206.59.45:/home/ec2-user/DainikBuddy/
```

**Step 2:** SSH into EC2 and restart:
```powershell
ssh -i "d:\HACKON\PocketBuddy\.ssh\pocketbuddy-key.pem" ec2-user@54.206.59.45
```

**Step 3 (inside EC2):**
```bash
sudo systemctl restart pocketbuddy
sudo systemctl status pocketbuddy
```

---

## Scenario 3: Backend Changes via GitHub

**Step 1:** Push changes (LOCAL PowerShell):
```powershell
cd d:\HACKON\PocketBuddy
git add backend/
git commit -m "fix: describe your change"
git push origin main
```

**Step 2:** SSH into EC2:
```powershell
ssh -i "d:\HACKON\PocketBuddy\.ssh\pocketbuddy-key.pem" ec2-user@54.206.59.45
```

**Step 3 (inside EC2):**
```bash
cd /home/ec2-user/DainikBuddy
git pull origin main
sudo systemctl restart pocketbuddy
```

---

## Scenario 4: Edit Backend .env (API Keys, CORS, etc.)

**SSH into EC2:**
```powershell
ssh -i "d:\HACKON\PocketBuddy\.ssh\pocketbuddy-key.pem" ec2-user@54.206.59.45
```
```bash
nano /home/ec2-user/DainikBuddy/backend/.env
# Make changes, Ctrl+O to save, Ctrl+X to exit
sudo systemctl restart pocketbuddy
```

---

## Checking Logs

**SSH into EC2 first, then:**
```bash
# Live tail (follow new logs):
sudo journalctl -u pocketbuddy -f

# Last 50 lines:
sudo journalctl -u pocketbuddy -n 50

# Errors only:
sudo journalctl -u pocketbuddy -p err
```

---

## If Something Breaks

| Problem | Fix |
|---------|-----|
| Backend won't start | `sudo journalctl -u pocketbuddy -n 30` to see error |
| Frontend shows old version | Re-build + re-upload to S3 |
| CORS errors in browser | Edit `.env` on EC2, add S3 URL to CORS_ORIGINS, restart |
| EC2 instance rebooted | Backend auto-starts (systemd). But IP may change — check EC2 console |
| MongoDB connection fails | Whitelist `54.206.59.45` in Atlas Network Access (or use `0.0.0.0/0`) |

---

## Git Workflow Diagram

```
LOCAL MACHINE                          EC2 SERVER
─────────────                          ──────────
                                       
Edit frontend → npm build              
             → aws s3 sync ──────────▶ S3 Bucket (live)
                                       
Edit backend  → scp upload ──────────▶ /home/ec2-user/DainikBuddy/
             or                        sudo systemctl restart pocketbuddy
             → git push ────▶ GitHub ──▶ git pull on EC2
```
