#!/bin/bash

# Start MCP Servers for BarakhTraderLite
# This script starts all configured MCP servers

echo "🚀 Starting MCP servers for BarakhTraderLite..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found! Please run setup-mcp.sh first"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check if MCP CLI is installed
if ! command -v mcp-server &> /dev/null; then
    echo "❌ MCP CLI not found! Please run setup-mcp.sh first"
    exit 1
fi

# Start MCP servers
echo "🔧 Starting MCP servers with configuration..."
mcp-server start --config mcp_config.json

echo "✅ MCP servers started successfully!"
echo ""
echo "Available MCP servers:"
echo "- GitHub: Repository management and PR tracking"
echo "- Web Search: Real-time market data and news"
echo "- Memory: Persistent storage for trading strategies"
echo "- Filesystem: File and directory management"
echo "- Database: Trading data and analytics"
echo "- Terminal: Command-line operations"
echo "- Code Analysis: TypeScript/React code quality"
echo "- Fetch: HTTP requests and API calls"
echo "- SQLite: Local database operations"
echo ""
echo "Press Ctrl+C to stop all servers"


