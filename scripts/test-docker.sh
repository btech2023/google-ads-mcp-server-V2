#!/bin/bash
# Script to test the Docker container locally

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
curl -s http://localhost:8000/health | grep -q "status"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Health check passed!${NC}"
else
    echo -e "${RED}Health check failed!${NC}"
    docker logs google-ads-mcp-test
    echo -e "${YELLOW}Stopping container...${NC}"
    docker stop google-ads-mcp-test
    docker rm google-ads-mcp-test
    exit 1
fi

echo -e "${GREEN}Container is healthy. Running for 10 seconds...${NC}"
sleep 10

echo -e "${YELLOW}Stopping container...${NC}"
docker stop google-ads-mcp-test
docker rm google-ads-mcp-test

echo -e "${GREEN}Test completed successfully!${NC}" 