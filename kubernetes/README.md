# Kubernetes Deployment for Google Ads MCP Server

This directory contains Kubernetes manifests for deploying the Google Ads MCP Server to Google Kubernetes Engine (GKE).

## Directory Structure

```
kubernetes/
├── base/                     # Base Kubernetes manifests
│   ├── deployment.yaml       # Base deployment configuration
│   ├── kustomization.yaml    # Kustomize configuration for base
│   ├── secret-template.yaml  # Template for creating secrets (not used directly)
│   └── service.yaml          # Service configuration
├── overlays/                 # Environment-specific overlays
│   ├── dev/                  # Development environment
│   │   └── kustomization.yaml
│   ├── test/                 # Test environment
│   │   ├── kustomization.yaml
│   │   └── patches/
│   │       └── deployment-patch.yaml
│   └── prod/                 # Production environment
│       └── kustomization.yaml
└── README.md                 # This file
```

## Deployment Architecture

The Google Ads MCP Server is deployed with the following components:

1. **Deployment**: Manages the pods running the application
   - Uses a multi-container setup with the main application container
   - Configured with proper resource limits and health checks
   - Runs with 2 replicas for high availability

2. **Service**: Exposes the application to the cluster or externally
   - Uses ClusterIP type for internal access
   - Exposes port 80 mapped to container port 8000

3. **Secrets**: Stores sensitive Google Ads API credentials
   - Created via kubectl command in the CI/CD pipeline
   - Referenced by the deployment for secure access

## Environments

### Development (dev)
- Used for development and testing
- Minimal resources allocated

### Test (test)
- Used for integration testing
- Configured with test-specific environment variables

### Production (prod)
- Used for production deployment
- Will be configured with higher resource limits and replicas

## Deployment Process

The deployment process is automated using GitHub Actions:

1. A Docker image is built and pushed to Google Container Registry
2. Kustomize is used to generate environment-specific manifests
3. kubectl applies the manifests to the appropriate namespace
4. A health check verifies the deployment was successful

## Manual Deployment

If you need to deploy manually, you can use the following commands:

```bash
# Set up credentials
gcloud container clusters get-credentials google-ads-mcp-cluster --region us-central1

# Create the namespace
kubectl create namespace test

# Create the secret
kubectl create secret generic google-ads-credentials \
  --namespace=test \
  --from-literal=GOOGLE_ADS_DEVELOPER_TOKEN=your-token \
  --from-literal=GOOGLE_ADS_CLIENT_ID=your-client-id \
  --from-literal=GOOGLE_ADS_CLIENT_SECRET=your-client-secret \
  --from-literal=GOOGLE_ADS_REFRESH_TOKEN=your-refresh-token \
  --from-literal=GOOGLE_ADS_LOGIN_CUSTOMER_ID=your-customer-id

# Deploy using kustomize
kubectl apply -k kubernetes/overlays/test
```

## Troubleshooting

If you encounter issues with the deployment, you can check the status of the resources:

```bash
# Check pods
kubectl get pods -n test

# Check logs
kubectl logs -n test -l app=google-ads-mcp-server

# Check service
kubectl get svc -n test

# Check deployment
kubectl describe deployment -n test google-ads-mcp-server
``` 