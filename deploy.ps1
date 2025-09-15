# PowerShell script to deploy AI Assistant to Google Cloud Artifact Registry

# Configuration
$Registry = "europe-central2-docker.pkg.dev/ai-assistant-456219/ai-assistant"
$BackendImage = "$Registry/ai-assistant-backend:latest"
$FrontendImage = "$Registry/ai-assistant-frontend:latest"

Write-Host "Starting AI Assistant deployment..." -ForegroundColor Green

# Check Docker
Write-Host "Checking Docker..." -ForegroundColor Blue
docker version | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker not running" -ForegroundColor Red
    exit 1
}

# Clean up existing images
Write-Host "Cleaning up existing images..." -ForegroundColor Blue
docker images --format "{{.Repository}}:{{.Tag}}" | Where-Object { $_ -match "ai-assistant" } | ForEach-Object {
    docker rmi $_ --force 2>$null
}

# Build backend image
Write-Host "Building backend image..." -ForegroundColor Blue
docker build -t ai-assistant-backend:latest .
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: Backend build failed" -ForegroundColor Red; exit 1 }

# Build frontend image
Write-Host "Building frontend image..." -ForegroundColor Blue
Set-Location frontend
docker build -t ai-assistant-frontend:latest .
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: Frontend build failed" -ForegroundColor Red; exit 1 }
Set-Location ..

# Tag images
Write-Host "Tagging images..." -ForegroundColor Blue
docker tag ai-assistant-backend:latest $BackendImage
docker tag ai-assistant-frontend:latest $FrontendImage

# Configure GCP authentication
Write-Host "Configuring GCP authentication..." -ForegroundColor Blue
gcloud auth configure-docker europe-central2-docker.pkg.dev --quiet

# Push images
Write-Host "Pushing backend image..." -ForegroundColor Blue
docker push $BackendImage
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: Backend push failed" -ForegroundColor Red; exit 1 }

Write-Host "Pushing frontend image..." -ForegroundColor Blue
docker push $FrontendImage
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: Frontend push failed" -ForegroundColor Red; exit 1 }

Write-Host "Deployment completed successfully!" -ForegroundColor Green