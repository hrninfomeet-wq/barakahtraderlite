"use client";

import { useState, useEffect } from 'react';

interface APITestResult {
  broker: string;
  endpoint: string;
  status: 'success' | 'error' | 'pending';
  response?: any;
  error?: string;
  responseTime?: number;
}

interface MarketDataTest {
  symbol: string;
  brokers: string[];
  results: APITestResult[];
}

export default function APITestPage() {
  const [testResults, setTestResults] = useState<APITestResult[]>([]);
  const [marketDataTests, setMarketDataTests] = useState<MarketDataTest[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedBrokers, setSelectedBrokers] = useState<string[]>(['upstox', 'fyers', 'aliceblue']);
  const [testSymbols, setTestSymbols] = useState<string>('NIFTY,TCS,RELIANCE');

  const testAPIEndpoint = async (broker: string, endpoint: string): Promise<APITestResult> => {
    const startTime = Date.now();
    
    try {
      const response = await fetch(`/api/v1/auth/${broker}/status`);
      const responseTime = Date.now() - startTime;
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      return {
        broker,
        endpoint,
        status: 'success',
        response: data,
        responseTime
      };
    } catch (error) {
      return {
        broker,
        endpoint,
        status: 'error',
        error: error instanceof Error ? error.message : 'Unknown error',
        responseTime: Date.now() - startTime
      };
    }
  };

  const testMarketData = async (symbols: string[], brokers: string[]) => {
    const tests: MarketDataTest[] = [];
    
    for (const symbol of symbols) {
      const results: APITestResult[] = [];
      
      for (const broker of brokers) {
        const startTime = Date.now();
        
        try {
          // Test market data endpoint
          const response = await fetch(`/api/v1/market-data/batch?symbols=${symbol}&live_data_enabled=true`);
          const responseTime = Date.now() - startTime;
          
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }
          
          const data = await response.json();
          
          results.push({
            broker,
            endpoint: `/api/v1/market-data/batch`,
            status: 'success',
            response: data,
            responseTime
          });
        } catch (error) {
          results.push({
            broker,
            endpoint: `/api/v1/market-data/batch`,
            status: 'error',
            error: error instanceof Error ? error.message : 'Unknown error',
            responseTime: Date.now() - startTime
          });
        }
      }
      
      tests.push({
        symbol,
        brokers,
        results
      });
    }
    
    setMarketDataTests(tests);
  };

  const runComprehensiveTests = async () => {
    setLoading(true);
    setTestResults([]);
    setMarketDataTests([]);

    // Test broker authentication status
    const authTests = await Promise.all(
      selectedBrokers.map(broker => testAPIEndpoint(broker, '/api/v1/auth/{broker}/status'))
    );

    setTestResults(authTests);

    // Test market data with multiple symbols
    const symbols = testSymbols.split(',').map(s => s.trim()).filter(s => s);
    if (symbols.length > 0) {
      await testMarketData(symbols, selectedBrokers);
    }

    setLoading(false);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'text-green-600 bg-green-50 border-green-200';
      case 'error': return 'text-red-600 bg-red-50 border-red-200';
      case 'pending': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return '✅';
      case 'error': return '❌';
      case 'pending': return '⏳';
      default: return '❓';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">API Integration Test Suite</h1>
          <p className="text-xl text-gray-600">Comprehensive Multi-Broker API Testing</p>
        </div>

        {/* Test Configuration */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-2xl font-semibold mb-4">Test Configuration</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Brokers to Test:
              </label>
              <div className="space-y-2">
                {['upstox', 'fyers', 'aliceblue', 'flattrade'].map(broker => (
                  <label key={broker} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={selectedBrokers.includes(broker)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedBrokers([...selectedBrokers, broker]);
                        } else {
                          setSelectedBrokers(selectedBrokers.filter(b => b !== broker));
                        }
                      }}
                      className="mr-2"
                    />
                    <span className="capitalize">{broker}</span>
                  </label>
                ))}
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Test Symbols (comma-separated):
              </label>
              <input
                type="text"
                value={testSymbols}
                onChange={(e) => setTestSymbols(e.target.value)}
                placeholder="NIFTY,TCS,RELIANCE"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
          
          <div className="mt-6 text-center">
            <button
              onClick={runComprehensiveTests}
              disabled={loading || selectedBrokers.length === 0}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed text-white font-medium py-3 px-8 rounded-lg transition-colors"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Running Tests...
                </span>
              ) : (
                '🚀 Run Comprehensive Tests'
              )}
            </button>
          </div>
        </div>

        {/* Authentication Test Results */}
        {testResults.length > 0 && (
          <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h2 className="text-2xl font-semibold mb-4">Authentication Status Tests</h2>
            
            <div className="grid grid-cols-1 gap-4">
              {testResults.map((result, index) => (
                <div key={index} className={`border rounded-lg p-4 ${getStatusColor(result.status)}`}>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold capitalize">{result.broker}</h3>
                    <span className="flex items-center">
                      {getStatusIcon(result.status)} {result.status}
                      {result.responseTime && (
                        <span className="ml-2 text-xs">({result.responseTime}ms)</span>
                      )}
                    </span>
                  </div>
                  
                  {result.status === 'success' && result.response && (
                    <div className="text-sm">
                      <div>Status: {result.response.status}</div>
                      <div>Requires Login: {result.response.requires_login ? 'Yes' : 'No'}</div>
                      <div>Has API Key: {result.response.has_credentials ? 'Yes' : 'No'}</div>
                      <div>Has Access Token: {result.response.has_access_token ? 'Yes' : 'No'}</div>
                    </div>
                  )}
                  
                  {result.status === 'error' && result.error && (
                    <div className="text-sm text-red-600">
                      Error: {result.error}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Market Data Test Results */}
        {marketDataTests.length > 0 && (
          <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h2 className="text-2xl font-semibold mb-4">Market Data Tests</h2>
            
            {marketDataTests.map((test, index) => (
              <div key={index} className="mb-6">
                <h3 className="text-lg font-semibold mb-3">Symbol: {test.symbol}</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {test.results.map((result, resultIndex) => (
                    <div key={resultIndex} className={`border rounded-lg p-4 ${getStatusColor(result.status)}`}>
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium capitalize">{result.broker}</h4>
                        <span className="flex items-center">
                          {getStatusIcon(result.status)} {result.status}
                          {result.responseTime && (
                            <span className="ml-2 text-xs">({result.responseTime}ms)</span>
                          )}
                        </span>
                      </div>
                      
                      {result.status === 'success' && result.response && (
                        <div className="text-sm space-y-1">
                          <div>Success: {result.response.success ? 'Yes' : 'No'}</div>
                          {result.response.data && result.response.data[test.symbol] && (
                            <>
                              <div>Price: ₹{result.response.data[test.symbol].last_price || 'N/A'}</div>
                              <div>Change: {result.response.data[test.symbol].change_percent || 'N/A'}%</div>
                              <div>Source: {result.response.data[test.symbol].source || 'N/A'}</div>
                            </>
                          )}
                        </div>
                      )}
                      
                      {result.status === 'error' && result.error && (
                        <div className="text-sm text-red-600">
                          Error: {result.error}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Test Summary */}
        {(testResults.length > 0 || marketDataTests.length > 0) && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-semibold mb-4">Test Summary</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {selectedBrokers.length}
                </div>
                <div className="text-sm text-blue-600">Brokers Tested</div>
              </div>
              
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {[...testResults, ...marketDataTests.flatMap(t => t.results)].filter(r => r.status === 'success').length}
                </div>
                <div className="text-sm text-green-600">Successful Tests</div>
              </div>
              
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <div className="text-2xl font-bold text-red-600">
                  {[...testResults, ...marketDataTests.flatMap(t => t.results)].filter(r => r.status === 'error').length}
                </div>
                <div className="text-sm text-red-600">Failed Tests</div>
              </div>
              
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {testSymbols.split(',').length}
                </div>
                <div className="text-sm text-purple-600">Symbols Tested</div>
              </div>
            </div>
          </div>
        )}

        <div className="text-center mt-8">
          <button
            onClick={() => window.location.href = '/'}
            className="bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-6 rounded-lg transition-colors mr-4"
          >
            ← Back to Dashboard
          </button>
          
          <button
            onClick={runComprehensiveTests}
            disabled={loading}
            className="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-6 rounded-lg transition-colors"
          >
            🔄 Re-run Tests
          </button>
        </div>
      </div>
    </div>
  );
}

