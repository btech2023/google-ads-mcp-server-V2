# Google Ads MCP Server

*Updated on March 21, 2024 - Triggering workflow run*

A Model Context Protocol (MCP) server that provides access to Google Ads data through Claude Desktop.

## Features

- Access Google Ads campaigns, accounts, and performance metrics via Claude
- Support for both Manager (MCC) and client account data
- Built-in caching to improve performance and reduce API calls
- Claude Artifacts integration for data visualization
- Multi-environment support (development, testing, production)
- Containerized deployment with Docker

## Prerequisites

- Python 3.9 or higher
- Google Ads API credentials
- Claude Desktop

## Quick Start

### Local Development

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/google-ads-mcp.git
   cd google-ads-mcp
   ```

2. Set up a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your Google Ads credentials:
   ```
   cp .env.example .env
   # Edit .env file with your credentials
   ```

5. Run the server:
   ```
   python server.py
   ```

### Docker Deployment

1. Build the Docker image:
   ```
   docker build -t google-ads-mcp:latest .
   ```

2. Run the container:
   ```
   docker run -p 8000:8000 --env-file .env google-ads-mcp:latest
   ```

Alternatively, use docker-compose:
   ```
   docker-compose up -d
   ```

## Configuration

The application supports different environments (dev, test, prod) with environment-specific configurations:

- Set `APP_ENV` to `dev`, `test`, or `prod` to specify the environment
- Configure environment variables as documented in `.env.example`
- Feature flags allow enabling/disabling specific functionality

## Claude Desktop Integration

1. Configure Claude Desktop for the MCP server in your Claude Desktop App configuration:
   ```json
   {
       "mcpServers": {
           "google-ads": {
               "command": "python",
               "args": [
                   "/absolute/path/to/server.py"
               ]
           }
       }
   }
   ```

2. Restart Claude Desktop and look for the tools icon to appear

3. Use Google Ads data in Claude by asking questions like:
   - "Show me my Google Ads account performance"
   - "What campaigns are performing well in my account?"
   - "Create a visualization of my campaign performance"

## Deployment

This repository includes Kubernetes manifests for deployment:

- `kubernetes/dev/` - Development environment deployment
- `kubernetes/test/` - Test environment deployment
- `kubernetes/prod/` - Production environment deployment

CI/CD pipelines are configured using GitHub Actions for automated testing, building, and deployment.

## Security

- All credentials are stored in Kubernetes secrets or environment variables, never in code
- The server uses proper authentication for API access
- Rate limiting is enabled in production environments
- Container security best practices are followed

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Google Ads API team for their documentation and support
- Anthropic for Claude and the Model Context Protocol 