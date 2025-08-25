# 🚀 Azure Deployment Guide

## 📋 Prerequisites
- Azure CLI installed
- Docker installed
- Azure subscription with appropriate permissions

## 🔧 Environment Setup

1. **Copy and configure environment variables:**
```bash
cp .env.azure.example .env.azure
```

2. **Edit `.env.azure` with your Azure credentials:**
- Update `COSMOS_ENDPOINT` and `COSMOS_KEY`
- Set `JWT_SECRET` to a strong secret key
- Configure Azure Storage connection string
- Customize app names and resource group if needed

## 🚀 Deployment Options

### Option 1: PowerShell (Windows)
```powershell
# Load environment variables
Get-Content .env.azure | foreach {
    $name, $value = $_.split('=')
    if ($name -and $value) {
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

# Run deployment
.\azure-deploy.ps1
```

### Option 2: Bash (Linux/Mac)
```bash
# Load environment variables
export $(cat .env.azure | xargs)

# Make script executable and run
chmod +x azure-deploy.sh
./azure-deploy.sh
```

## 🧪 Local Testing

### Test with Docker Compose:
```bash
# Local development
docker-compose up --build

# Test Azure configuration locally
docker-compose -f docker-compose.azure.yml up --build
```

## 📊 Monitoring & Health Checks

Both services include health check endpoints:
- Backend: `https://your-backend-app.azurewebsites.net/health`
- Frontend: `https://your-frontend-app.azurewebsites.net/health`

## 🔄 CI/CD Integration

You can integrate these Docker files with Azure DevOps or GitHub Actions for automated deployments.

## 📝 Post-Deployment

After successful deployment:
1. Update your frontend configuration to point to the new backend URL
2. Configure custom domains if needed
3. Set up monitoring and alerts
4. Configure SSL certificates (Azure App Service provides free SSL)

## 🛠️ Troubleshooting

If deployment fails:
1. Check Azure CLI authentication: `az account show`
2. Verify Docker is running: `docker --version`
3. Check environment variables are set correctly
4. Review Azure portal for detailed error messages
