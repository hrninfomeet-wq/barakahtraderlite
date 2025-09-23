"use client";

import { useState, useEffect } from 'react';

interface BrokerStatus {
  provider: string;
  status: string;
  has_api_key?: boolean;
  has_access_token?: boolean;
  requires_login?: boolean;
}

export default function Home() {
  const [brokerStatuses, setBrokerStatuses] = useState<Record<string, BrokerStatus>>({});
  const [loading, setLoading] = useState(true);
  const [authenticating, setAuthenticating] = useState<string | null>(null);

  const fetchBrokerStatuses = async () => {
    try {
      const brokers = ['upstox', 'flattrade', 'fyers', 'aliceblue'];
      const promises = brokers.map(async (broker) => {
        try {
          const response = await fetch(`/api/v1/auth/${broker}/status`);
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
          }
          const text = await response.text();
          const data = text ? JSON.parse(text) : {};
          return { broker, data };
        } catch (error) {
          console.error(`Error fetching ${broker} status:`, error);
          return { broker, data: { provider: broker, status: 'error', requires_login: true } };
        }
      });
      
      const results = await Promise.all(promises);
      const statuses: Record<string, BrokerStatus> = {};
      
      results.forEach(({ broker, data }) => {
        statuses[broker] = data;
      });
      
      setBrokerStatuses(statuses);
    } catch (error) {
      console.error('Error fetching broker statuses:', error);
    } finally {
      setLoading(false);
    }
  };

  const authenticateBroker = async (broker: string) => {
    setAuthenticating(broker);
    try {
      const response = await fetch(`/api/v1/auth/${broker}/login`);
      const data = await response.json();
      
      if (data.auth_url) {
        // Open OAuth URL in a popup window
        const popup = window.open(
          data.auth_url,
          `${broker}_auth`,
          'width=700,height=800,scrollbars=yes,resizable=yes,location=yes'
        );
        
        // Listen for postMessage from popup (for successful auth)
        const messageListener = (event: MessageEvent) => {
          if (event.data.type === `${broker.toUpperCase()}_AUTH_SUCCESS`) {
            console.log(`${broker} authentication successful!`);
            popup?.close();
            setAuthenticating(null);
            fetchBrokerStatuses();
            window.removeEventListener('message', messageListener);
          } else if (event.data.type === `${broker.toUpperCase()}_AUTH_ERROR`) {
            console.error(`${broker} authentication failed:`, event.data.error);
            popup?.close();
            setAuthenticating(null);
            window.removeEventListener('message', messageListener);
          }
        };
        
        window.addEventListener('message', messageListener);
        
        // Also listen for popup closure
        const checkClosed = setInterval(() => {
          if (popup?.closed) {
            clearInterval(checkClosed);
            setAuthenticating(null);
            window.removeEventListener('message', messageListener);
            // Refresh statuses after authentication attempt
            setTimeout(fetchBrokerStatuses, 1000);
          }
        }, 1000);
        
        // Auto-close popup after 5 minutes if not closed
        setTimeout(() => {
          if (popup && !popup.closed) {
            popup.close();
            clearInterval(checkClosed);
            setAuthenticating(null);
            window.removeEventListener('message', messageListener);
          }
        }, 300000);
      }
    } catch (error) {
      console.error(`Error authenticating ${broker}:`, error);
      setAuthenticating(null);
    }
  };

  useEffect(() => {
    fetchBrokerStatuses();
    // Refresh statuses every 30 seconds
    const interval = setInterval(fetchBrokerStatuses, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'authenticated': return 'text-green-600 bg-green-50';
      case 'disconnected': return 'text-yellow-600 bg-yellow-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'authenticated': return '✅';
      case 'disconnected': return '⚠️';
      default: return '❓';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading broker statuses...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Barakah Trader Lite</h1>
          <p className="text-xl text-gray-600">Multi-Broker Authentication Dashboard</p>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-2xl font-semibold mb-6 text-center">Broker Connection Status</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {Object.entries(brokerStatuses).map(([broker, status]) => (
              <div key={broker} className="border rounded-lg p-6 hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-semibold capitalize text-gray-900">{broker}</h3>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(status.status)}`}>
                    {getStatusIcon(status.status)} {status.status}
                  </span>
                </div>
                
                <div className="space-y-2 mb-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">API Key:</span>
                    <span>{status.has_api_key ? '✅ Configured' : '❌ Missing'}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Access Token:</span>
                    <span>{status.has_access_token ? '✅ Active' : '❌ Not Set'}</span>
                  </div>
                </div>
                
                {status.requires_login ? (
                  <button
                    onClick={() => authenticateBroker(broker)}
                    disabled={authenticating === broker}
                    className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed text-white font-medium py-2 px-4 rounded-lg transition-colors"
                  >
                    {authenticating === broker ? (
                      <span className="flex items-center justify-center">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Authenticating...
                      </span>
                    ) : (
                      `Connect to ${broker.charAt(0).toUpperCase() + broker.slice(1)}`
                    )}
                  </button>
                ) : status.status === 'authenticated' ? (
                  <div className="text-center">
                    <div className="text-green-600 font-medium mb-2">
                      ✅ Ready for Trading
                    </div>
                    <button
                      onClick={() => authenticateBroker(broker)}
                      disabled={authenticating === broker}
                      className="w-full bg-green-600 hover:bg-green-700 disabled:bg-green-400 disabled:cursor-not-allowed text-white font-medium py-2 px-4 rounded-lg transition-colors text-sm"
                    >
                      🔄 Re-authenticate
                    </button>
                  </div>
                ) : (
                  <div className="text-center text-gray-500">
                    Configuration Needed
                  </div>
                )}
                
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-2xl font-semibold mb-4">System Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {Object.values(brokerStatuses).filter(s => s.status === 'authenticated').length}
              </div>
              <div className="text-sm text-green-600">Connected Brokers</div>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">PAPER</div>
              <div className="text-sm text-blue-600">Trading Mode</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">LIVE</div>
              <div className="text-sm text-purple-600">Market Data</div>
            </div>
          </div>
        </div>
        
        <div className="text-center mt-8">
          <button
            onClick={fetchBrokerStatuses}
            className="bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-6 rounded-lg transition-colors"
          >
            🔄 Refresh Status
          </button>
        </div>
      </div>
    </div>
  );
}
