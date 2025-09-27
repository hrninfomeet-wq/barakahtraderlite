# MCP Servers for BarakhTraderLite

This document explains the MCP (Model Context Protocol) servers configured for your AI-powered Indian trading engine project.

## Configured MCP Servers

### 1. **GitHub MCP Server** (`@modelcontextprotocol/server-github`)
- **Purpose**: Repository management, PR tracking, issue management
- **Benefits for Trading Project**:
  - Track development progress and milestones
  - Manage pull requests for trading strategy implementations
  - Monitor issues and bug reports
  - Access repository analytics and insights

### 2. **Web Search MCP Server** (`@modelcontextprotocol/server-web-search`)
- **Purpose**: Real-time web search and market data retrieval
- **Benefits for Trading Project**:
  - Fetch real-time market news and sentiment
  - Research Indian market trends and analysis
  - Get latest financial data and economic indicators
  - Access trading strategy documentation and tutorials

### 3. **Memory MCP Server** (`@modelcontextprotocol/server-memory`)
- **Purpose**: Persistent memory storage for AI context
- **Benefits for Trading Project**:
  - Store trading strategies and configurations
  - Remember market patterns and analysis
  - Maintain conversation context across sessions
  - Store user preferences and trading rules

### 4. **Filesystem MCP Server** (`@modelcontextprotocol/server-filesystem`)
- **Purpose**: File and directory management
- **Benefits for Trading Project**:
  - Manage trading data files and logs
  - Organize strategy files and configurations
  - Handle backup and restore operations
  - Manage project documentation

### 5. **Database MCP Server** (`@modelcontextprotocol/server-database`)
- **Purpose**: Database operations and management
- **Benefits for Trading Project**:
  - Store trading history and performance data
  - Manage user accounts and API configurations
  - Handle real-time market data storage
  - Support backtesting and analytics

### 6. **Terminal MCP Server** (`@modelcontextprotocol/server-terminal`)
- **Purpose**: Command-line operations
- **Benefits for Trading Project**:
  - Run development and testing commands
  - Execute trading scripts and algorithms
  - Manage system processes and monitoring
  - Handle deployment and maintenance tasks

### 7. **Code Analysis MCP Server** (`@modelcontextprotocol/server-code-analysis`)
- **Purpose**: Code quality and analysis
- **Benefits for Trading Project**:
  - Analyze TypeScript/React code quality
  - Detect potential bugs in trading algorithms
  - Ensure code compliance and best practices
  - Optimize performance and maintainability

### 8. **Fetch MCP Server** (`@modelcontextprotocol/server-fetch`)
- **Purpose**: HTTP requests and API calls
- **Benefits for Trading Project**:
  - Make API calls to trading brokers (FLATTRADE, FYERS, UPSTOX)
  - Fetch market data from various sources
  - Handle authentication and rate limiting
  - Manage external service integrations

### 9. **SQLite MCP Server** (`@modelcontextprotocol/server-sqlite`)
- **Purpose**: SQLite database operations
- **Benefits for Trading Project**:
  - Local database for trading data
  - Store historical market data
  - Manage user preferences and settings
  - Support offline trading analysis

## Setup Instructions

### 1. Install MCP CLI and Servers
```bash
npm run mcp:install
```

### 2. Configure Environment Variables
Copy `env.example` to `.env` and fill in your API keys:
```bash
cp env.example .env
```

### 3. Start MCP Servers
```bash
npm run mcp:start
```

## API Keys Required

### Essential for Trading Project:
- **GitHub Personal Access Token**: For repository management
- **Brave Search API Key**: For web search and market data
- **Trading API Keys**: FLATTRADE, FYERS, UPSTOX, Alice Blue
- **AI Service Keys**: Google Gemini Pro, optional OpenAI/Anthropic

### Optional but Recommended:
- **NSE/BSE/MCX API Keys**: For direct market data access
- **Additional AI Service Keys**: For enhanced analysis capabilities

## Usage Examples

### For Trading Strategy Development:
```typescript
// Use Memory MCP to store strategy configurations
await memory.store("btst_strategy", {
  confidence_threshold: 8.5,
  max_position_size: 0.1,
  stop_loss_percentage: 2.0
});

// Use Web Search MCP to get market news
const marketNews = await webSearch.search("NIFTY 50 market analysis today");

// Use Database MCP to store trading data
await database.query("INSERT INTO trades (symbol, quantity, price) VALUES (?, ?, ?)", 
  ["NIFTY", 100, 19500]);
```

### For Development Workflow:
```typescript
// Use GitHub MCP to create issues for trading features
await github.createIssue({
  title: "Implement Iron Condor Strategy",
  body: "Add automated Iron Condor options strategy with Greeks calculation"
});

// Use Code Analysis MCP to check trading algorithm quality
const analysis = await codeAnalysis.analyzeFile("src/strategies/btst.ts");

// Use Terminal MCP to run tests
await terminal.execute("npm test -- --grep 'F&O strategies'");
```

## Security Considerations

1. **API Key Management**: Store all API keys securely in `.env` file
2. **Rate Limiting**: Be aware of API rate limits for trading brokers
3. **Data Privacy**: Ensure sensitive trading data is properly encrypted
4. **Access Control**: Limit filesystem access to project directory only

## Troubleshooting

### Common Issues:
1. **MCP Server Connection Failed**: Check API keys and network connectivity
2. **Rate Limit Exceeded**: Implement proper rate limiting and caching
3. **Database Connection Error**: Verify SQLite database path and permissions
4. **File Access Denied**: Check filesystem permissions and allowed directories

### Support:
- Check MCP server logs for detailed error messages
- Verify environment variables are correctly set
- Ensure all required dependencies are installed
- Check network connectivity for external API calls

## Next Steps

1. **Configure API Keys**: Set up all required API keys in `.env`
2. **Test MCP Servers**: Verify all servers are working correctly
3. **Integrate with Trading Platform**: Use MCP servers in your trading application
4. **Monitor Performance**: Track MCP server usage and optimize as needed

This MCP setup provides comprehensive support for your AI-powered Indian trading engine, enabling advanced development, real-time market data access, and intelligent trading strategy management.


