#!/bin/bash
# Script to test the Docker container's health check

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building Docker image...${NC}"
docker build -t google-ads-mcp:test .

if [ $? -ne 0 ]; then
    echo -e "${RED}Docker build failed!${NC}"
    exit 1
fi

echo -e "${GREEN}Starting Docker container...${NC}"
docker run --name google-ads-mcp-test -p 8000:8000 --env-file .env -d google-ads-mcp:test

if [ $? -ne 0 ]; then
    echo -e "${RED}Docker run failed!${NC}"
    exit 1
fi

echo -e "${GREEN}Container started! Waiting for it to initialize...${NC}"
sleep 5

echo -e "${GREEN}Testing health endpoint...${NC}"
HEALTH_CHECK=$(curl -s http://localhost:8000/health)
echo $HEALTH_CHECK | jq . || echo $HEALTH_CHECK

# Check if health status is OK
if echo $HEALTH_CHECK | grep -q '"status":"OK"'; then
    echo -e "${GREEN}Health check passed!${NC}"
else
    echo -e "${RED}Health check failed!${NC}"
    echo -e "${YELLOW}Container logs:${NC}"
    docker logs google-ads-mcp-test
    echo -e "${YELLOW}Stopping container...${NC}"
    docker stop google-ads-mcp-test
    docker rm google-ads-mcp-test
    exit 1
fi

echo -e "${GREEN}Testing MCP health tool via curl...${NC}"
TOOL_DATA='{"tool":"get_health_status","args":{}}'
curl -s -X POST -H "Content-Type: application/json" -d "$TOOL_DATA" http://localhost:8000/mcp/v1/tools/call

echo -e "\n\n${GREEN}Container is healthy. Running for 10 seconds...${NC}"
sleep 10

echo -e "${YELLOW}Stopping container...${NC}"
docker stop google-ads-mcp-test
docker rm google-ads-mcp-test

echo -e "${GREEN}Test completed successfully!${NC}" 