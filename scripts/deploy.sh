#!/bin/bash
# Deployment script for Google Ads MCP Server
# Usage: ./deploy.sh [environment] [version]
# Example: ./deploy.sh dev v1.0.0

set -e

# Default values
ENV=${1:-dev}
VERSION=${2:-latest}
NAMESPACE=${ENV}
REPO="ghcr.io/your-username/google-ads-mcp"
MANIFESTS_DIR="kubernetes/${ENV}"

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print header
echo -e "${GREEN}========================================"
echo -e "Google Ads MCP Server Deployment"
echo -e "Environment: ${YELLOW}${ENV}${GREEN}"
echo -e "Version: ${YELLOW}${VERSION}${GREEN}"
echo -e "========================================${NC}"

# Check if kubeconfig is accessible
if [ -z "${KUBECONFIG}" ]; then
    echo -e "${YELLOW}KUBECONFIG not set, using default config${NC}"
fi

# Check if required tools are installed
for cmd in kubectl docker sed; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${RED}Error: $cmd is not installed${NC}"
        exit 1
    fi
done

# Check if manifests directory exists
if [ ! -d "${MANIFESTS_DIR}" ]; then
    echo -e "${RED}Error: Manifests directory ${MANIFESTS_DIR} not found${NC}"
    exit 1
fi

# Perform deployment
echo -e "${GREEN}Starting deployment process...${NC}"

# 1. Update image tag in manifests
echo -e "${GREEN}Updating image tag to ${VERSION}...${NC}"
sed -i.bak "s|IMAGE_TAG|${VERSION}|g" ${MANIFESTS_DIR}/deployment.yaml
rm -f ${MANIFESTS_DIR}/deployment.yaml.bak

# 2. Apply Kubernetes manifests
echo -e "${GREEN}Applying Kubernetes manifests...${NC}"
kubectl apply -f ${MANIFESTS_DIR}/

# 3. Wait for deployment to complete
echo -e "${GREEN}Waiting for deployment to complete...${NC}"
kubectl rollout status deployment/google-ads-mcp-server -n ${NAMESPACE} --timeout=120s

# 4. Verify deployment
echo -e "${GREEN}Verifying deployment...${NC}"
POD_COUNT=$(kubectl get pods -n ${NAMESPACE} -l app=google-ads-mcp-server --field-selector=status.phase=Running --no-headers | wc -l)
if [ "${POD_COUNT}" -gt 0 ]; then
    echo -e "${GREEN}Deployment successful! ${POD_COUNT} pod(s) running.${NC}"
    
    # Get service URL
    if kubectl get service -n ${NAMESPACE} google-ads-mcp-server &> /dev/null; then
        SERVICE_IP=$(kubectl get service -n ${NAMESPACE} google-ads-mcp-server -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
        if [ -n "${SERVICE_IP}" ]; then
            echo -e "${GREEN}Service available at: ${YELLOW}http://${SERVICE_IP}:8000${NC}"
        else
            CLUSTER_IP=$(kubectl get service -n ${NAMESPACE} google-ads-mcp-server -o jsonpath='{.spec.clusterIP}')
            echo -e "${GREEN}Service available within cluster at: ${YELLOW}http://${CLUSTER_IP}:8000${NC}"
        fi
    fi
else
    echo -e "${RED}Deployment failed! No pods running.${NC}"
    echo -e "${YELLOW}Check logs with: kubectl logs -n ${NAMESPACE} -l app=google-ads-mcp-server${NC}"
    exit 1
fi

echo -e "${GREEN}Deployment complete!${NC}" 