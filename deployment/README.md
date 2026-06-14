# PocketBuddy AWS Deployment Guide

## Architecture

```
┌─────────────────┐     ┌──────────────────────────────┐
│   CloudFront    │     │     EC2 t3.micro             │
│  (CDN + HTTPS)  │     │  ┌─────────────────────┐    │
│                 │     │  │ Nginx (port 80/443)  │    │
│  React build    │     │  │   ↓ reverse proxy    │    │
│  from S3 bucket │     │  │ Uvicorn (port 8000)  │    │
│                 │     │  │   ↓                   │    │
└─────────────────┘     │  │ FastAPI server.py     │    │
                        │  └─────────────────────┘    │
                        └──────────────────────────────┘
                                      ↓
                        ┌──────────────────────────────┐
                        │   MongoDB Atlas M0 (free)    │
                        │   (already configured)       │
                        └──────────────────────────────┘
```

## Cost: $0/month (AWS Free Tier)

| Service | Free Tier |
|---------|-----------|
| EC2 t3.micro | 750 hrs/mo (12 months) |
| S3 | 5 GB storage, 20K GET |
| CloudFront | 1 TB transfer, 10M requests |
| MongoDB Atlas M0 | Free forever |

## Prerequisites

- AWS account (free tier eligible)
- AWS CLI installed (`winget install Amazon.AWSCLI`)
- Your existing MongoDB Atlas URL works from anywhere (no IP whitelist issues)

## Deployment Steps

See the step-by-step scripts in this folder:
1. `deploy-frontend.sh` — Build React app + upload to S3 + create CloudFront
2. `ec2-setup.sh` — Script to run ON the EC2 instance after SSH
3. `nginx.conf` — Nginx reverse proxy config for the backend
4. `pocketbuddy.service` — Systemd service file for auto-restart

## Quick Reference

After deployment:
- Frontend URL: `https://<cloudfront-id>.cloudfront.net`
- Backend URL: `http://<ec2-public-ip>` (or HTTPS if you add certbot)
- API Docs: `http://<ec2-public-ip>/docs`
