#!/bin/bash

# MCP Setup Script for BarakhTraderLite
# This script sets up all necessary MCP servers for the trading project

echo "🚀 Setting up MCP servers for BarakhTraderLite..."

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p data/memory
mkdir -p data/logs
mkdir -p data/backups

# Install MCP CLI globally
echo "📦 Installing MCP CLI..."
npm install -g @modelcontextprotocol/cli

# Install MCP servers
echo "🔧 Installing MCP servers..."
npm install @modelcontextprotocol/server-github
npm install @modelcontextprotocol/server-web-search
npm install @modelcontextprotocol/server-memory
npm install @modelcontextprotocol/server-filesystem
npm install @modelcontextprotocol/server-database
npm install @modelcontextprotocol/server-terminal
npm install @modelcontextprotocol/server-code-analysis
npm install @modelcontextprotocol/server-fetch
npm install @modelcontextprotocol/server-sqlite

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env file and add your API keys!"
else
    echo "✅ .env file already exists"
fi

# Set up SQLite database
echo "🗄️  Setting up SQLite database..."
sqlite3 data/trading.db <<EOF
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    side TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    strategy TEXT,
    pnl REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    config TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS market_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    price REAL NOT NULL,
    volume INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);
CREATE INDEX IF NOT EXISTS idx_market_data_symbol ON market_data(symbol);
CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data(timestamp);
EOF

# Set permissions
echo "🔐 Setting up permissions..."
chmod +x scripts/setup-mcp.sh
chmod +x scripts/start-mcp.sh

echo "✅ MCP setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your API keys"
echo "2. Run 'npm run mcp:start' to start MCP servers"
echo "3. Test the setup with 'npm test'"
echo ""
echo "For more information, see README_MCP.md"


