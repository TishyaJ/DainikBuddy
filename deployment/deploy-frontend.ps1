# =============================================================================
# Frontend Deployment to S3 + CloudFront (PowerShell - run from project root)
# =============================================================================
#
# Prerequisites:
#   1. AWS CLI installed and configured: aws configure
#   2. S3 bucket created (see Step 1 below)
#
# Usage:
#   cd d:\HACKON\PocketBuddy
#   .\deployment\deploy-frontend.ps1
# =============================================================================

param(
    [string]$BucketName = "pocketbuddy-frontend",
    [string]$Region = "ap-south-1"
)

$ErrorActionPreference = "Stop"

Write-Host "=== PocketBuddy Frontend Deployment ===" -ForegroundColor Cyan

# --- Step 1: Build the frontend ---
Write-Host "`n[1/4] Building React app..." -ForegroundColor Yellow
Set-Location "frontend"

# Ensure backend URL points to your EC2 instance
# CHANGE THIS to your actual EC2 public IP or domain!
$env:REACT_APP_BACKEND_URL = "http://YOUR_EC2_PUBLIC_IP"

npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

Set-Location ".."
Write-Host "Build successful!" -ForegroundColor Green

# --- Step 2: Create S3 bucket (skip if exists) ---
Write-Host "`n[2/4] Ensuring S3 bucket exists..." -ForegroundColor Yellow
$bucketExists = aws s3api head-bucket --bucket $BucketName 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating bucket: $BucketName in $Region"
    aws s3api create-bucket `
        --bucket $BucketName `
        --region $Region `
        --create-bucket-configuration LocationConstraint=$Region
    
    # Enable static website hosting
    aws s3 website "s3://$BucketName" `
        --index-document index.html `
        --error-document index.html
    
    # Set bucket policy for public read (CloudFront will serve it)
    $policy = @"
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$BucketName/*"
        }
    ]
}
"@
    $policy | Out-File -Encoding utf8 -FilePath "bucket-policy.json"
    aws s3api put-bucket-policy --bucket $BucketName --policy file://bucket-policy.json
    Remove-Item "bucket-policy.json"
} else {
    Write-Host "Bucket already exists." -ForegroundColor Green
}

# --- Step 3: Upload build to S3 ---
Write-Host "`n[3/4] Uploading build to S3..." -ForegroundColor Yellow
aws s3 sync frontend/build/ "s3://$BucketName/" `
    --delete `
    --cache-control "max-age=86400" `
    --exclude "*.html" `
    --exclude "service-worker.js" `
    --exclude "manifest.json"

# HTML files with no-cache (so updates are immediate)
aws s3 sync frontend/build/ "s3://$BucketName/" `
    --exclude "*" `
    --include "*.html" `
    --include "service-worker.js" `
    --include "manifest.json" `
    --cache-control "no-cache, no-store, must-revalidate"

Write-Host "Upload complete!" -ForegroundColor Green

# --- Step 4: Show URLs ---
Write-Host "`n[4/4] Deployment complete!" -ForegroundColor Cyan
Write-Host ""
Write-Host "S3 Website URL:" -ForegroundColor Yellow
Write-Host "  http://$BucketName.s3-website.$Region.amazonaws.com"
Write-Host ""
Write-Host "Next: Create a CloudFront distribution pointing to this S3 bucket"
Write-Host "  for HTTPS and better performance. See deployment/README.md"
Write-Host ""
Write-Host "Or just use the S3 URL directly for the hackathon demo!" -ForegroundColor Green
