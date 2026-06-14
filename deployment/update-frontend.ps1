# =============================================================================
# Quick Frontend Update Script (PowerShell - run locally)
# Use after making frontend changes to push updates to S3
# =============================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$BucketName
)

$ErrorActionPreference = "Stop"

Write-Host "=== Updating PocketBuddy Frontend ===" -ForegroundColor Cyan

# Build
Write-Host "Building..." -ForegroundColor Yellow
Set-Location "frontend"
npm run build
if ($LASTEXITCODE -ne 0) { Write-Host "Build failed!" -ForegroundColor Red; exit 1 }
Set-Location ".."

# Upload
Write-Host "Uploading to S3..." -ForegroundColor Yellow
aws s3 sync frontend/build/ "s3://$BucketName/" --delete

Write-Host "`n✓ Frontend updated!" -ForegroundColor Green
Write-Host "  URL: http://$BucketName.s3-website.ap-south-1.amazonaws.com"

# Invalidate CloudFront cache (if using CloudFront)
# aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
