"use client";

/**
 * Broker API Connections - Barakah Trader Lite
 * Multi-broker authentication interface inspired by Zerodha Kite, Upstox Pro, TradingView
 */

import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/ui/page-header';
import { Card } from '@/components/ui/card';
import { Loader } from '@/components/ui/loader';

const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "https://1b7fd467-acf6-4bd1-9040-93062c84f787-00-2w14iyh83mugu.sisko.replit.dev:8000";

interface BrokerStatus {
  id: string;
  name: string;
  logo?: string;
  connected: boolean;
  valid: boolean;
  lastConnected?: string;
  features: string[];
  status: 'connected' | 'expired' | 'disconnected' | 'connecting' | 'error';
  color: string;
  description: string;
}

const brokerConfigs = [
  {
    id: 'upstox',
    name: 'Upstox',
    description: 'Leading discount broker with comprehensive API coverage',
    color: 'blue',
    features: ['Real-time data', 'Order execution', 'Portfolio tracking', 'Historical data'],
  },
  {
    id: 'flattrade',
    name: 'Flattrade',
    description: 'Zero brokerage with advanced trading features',
    color: 'green',
    features: ['Zero brokerage', 'Real-time quotes', 'Advanced orders', 'Options chain'],
  },
  {
    id: 'fyers',
    name: 'Fyers',
    description: 'Technology-focused broker with powerful APIs',
    color: 'purple',
    features: ['Advanced charting', 'Strategy backtesting', 'Portfolio analytics', 'Alerts'],
  },
  {
    id: 'aliceblue',
    name: 'AliceBlue',
    description: 'Reliable broker with comprehensive market coverage',
    color: 'orange',
    features: ['Market data', 'Order management', 'Fund management', 'Research'],
  },
];

const colorStyles = {
  blue: {
    connected: 'bg-blue-50 border-blue-200 text-blue-900',
    button: 'bg-blue-600 hover:bg-blue-700 text-white',
    status: 'text-blue-600 bg-blue-100',
    expired: 'bg-yellow-50 border-yellow-200 text-yellow-900',
    error: 'bg-red-50 border-red-200 text-red-900',
    logo: 'bg-blue-100 text-blue-600',
  },
  green: {
    connected: 'bg-green-50 border-green-200 text-green-900',
    button: 'bg-green-600 hover:bg-green-700 text-white',
    status: 'text-green-600 bg-green-100',
    expired: 'bg-yellow-50 border-yellow-200 text-yellow-900',
    error: 'bg-red-50 border-red-200 text-red-900',
    logo: 'bg-green-100 text-green-600',
  },
  purple: {
    connected: 'bg-purple-50 border-purple-200 text-purple-900',
    button: 'bg-purple-600 hover:bg-purple-700 text-white',
    status: 'text-purple-600 bg-purple-100',
    expired: 'bg-yellow-50 border-yellow-200 text-yellow-900',
    error: 'bg-red-50 border-red-200 text-red-900',
    logo: 'bg-purple-100 text-purple-600',
  },
  orange: {
    connected: 'bg-orange-50 border-orange-200 text-orange-900',
    button: 'bg-orange-600 hover:bg-orange-700 text-white',
    status: 'text-orange-600 bg-orange-100',
    expired: 'bg-yellow-50 border-yellow-200 text-yellow-900',
    error: 'bg-red-50 border-red-200 text-red-900',
    logo: 'bg-orange-100 text-orange-600',
  },
};

export default function BrokerAPIPage() {
  const [brokers, setBrokers] = useState<BrokerStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState<string | null>(null);
  const [message, setMessage] = useState<string>("");

  const fetchBrokerStatuses = async () => {
    setLoading(true);
    try {
      const statuses = await Promise.all(
        brokerConfigs.map(async (config) => {
          try {
            const response = await fetch(`${backendUrl}/api/v1/auth/${config.id}/status`);
            const data = await response.json();
            
            return {
              ...config,
              connected: data.has_access_token || data.status === 'authenticated',
              valid: data.has_credentials && !data.requires_login,
              lastConnected: data.last_connected,
              status: data.has_access_token 
                ? (data.has_credentials ? 'connected' : 'expired')
                : 'disconnected',
            } as BrokerStatus;
          } catch {
            return {
              ...config,
              connected: false,
              valid: false,
              status: 'error',
            } as BrokerStatus;
          }
        })
      );
      
      setBrokers(statuses);
    } catch (error) {
      setMessage("Failed to fetch broker connection statuses");
    } finally {
      setLoading(false);
    }
  };

  const connectBroker = async (brokerId: string) => {
    setConnecting(brokerId);
    try {
      const response = await fetch(`${backendUrl}/api/v1/auth/${brokerId}/login`);
      const data = await response.json();
      
      if (response.ok && data.auth_url) {
        const popup = window.open(
          data.auth_url,
          `${brokerId}_auth`,
          'width=500,height=700,scrollbars=yes,resizable=yes'
        );
        
        if (popup) {
          setMessage(`${brokerId.charAt(0).toUpperCase() + brokerId.slice(1)} login window opened. Please complete authentication.`);
          
          // Handle popup communication
          const handleMessage = (event: MessageEvent) => {
            if (event.data && event.data.type === `${brokerId.toUpperCase()}_AUTH_RESULT`) {
              if (event.data.success) {
                setMessage(`✅ ${brokerId.charAt(0).toUpperCase() + brokerId.slice(1)} connected successfully!`);
                fetchBrokerStatuses();
              } else {
                setMessage(`❌ ${brokerId.charAt(0).toUpperCase() + brokerId.slice(1)} authentication failed: ${event.data.error}`);
              }
              window.removeEventListener('message', handleMessage);
            }
          };
          
          window.addEventListener('message', handleMessage);
          
          // Check if popup is closed manually
          const checkClosed = setInterval(() => {
            if (popup.closed) {
              clearInterval(checkClosed);
              setMessage("Authentication window closed. Please try again if authentication wasn't completed.");
              window.removeEventListener('message', handleMessage);
            }
          }, 1000);
        } else {
          setMessage("Popup blocked. Please allow popups and try again.");
        }
      } else {
        setMessage(data.message || `Failed to get ${brokerId} login URL`);
      }
    } catch (error) {
      setMessage(`Failed to connect to ${brokerId}`);
    } finally {
      setConnecting(null);
    }
  };

  const disconnectBroker = async (brokerId: string) => {
    try {
      await fetch(`${backendUrl}/api/v1/auth/${brokerId}/disconnect`, {
        method: 'DELETE',
      });
      setMessage(`${brokerId.charAt(0).toUpperCase() + brokerId.slice(1)} disconnected successfully`);
      fetchBrokerStatuses();
    } catch {
      setMessage(`Failed to disconnect ${brokerId}`);
    }
  };

  useEffect(() => {
    fetchBrokerStatuses();
  }, []);

  if (loading) {
    return (
      <div className="p-6 max-w-6xl mx-auto">
        <PageHeader title="Broker API Connections" />
        <Loader message="Loading broker connection statuses..." />
      </div>
    );
  }

  const connectedCount = brokers.filter(b => b.connected && b.valid).length;
  const totalCount = brokers.length;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <PageHeader 
        title="Broker API Connections"
        subtitle="Connect to multiple brokers for redundant market data and trading capabilities"
      >
        <a 
          href="/"
          className="px-4 py-2 text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
        >
          ← Back to Trading
        </a>
      </PageHeader>

      {message && (
        <div className={`mb-6 p-4 rounded-lg ${
          message.includes('✅') ? 'bg-green-50 text-green-800 border border-green-200' :
          message.includes('❌') ? 'bg-red-50 text-red-800 border border-red-200' :
          'bg-blue-50 text-blue-800 border border-blue-200'
        }`}>
          {message}
        </div>
      )}

      {/* Connection Overview */}
      <Card className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold">Connection Overview</h3>
            <p className="text-gray-600">
              {connectedCount} of {totalCount} brokers connected
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={fetchBrokerStatuses}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              🔄 Refresh All
            </button>
            {connectedCount > 0 && (
              <div className="px-3 py-2 bg-green-100 text-green-800 rounded-lg font-semibold">
                ✓ Live Data Active
              </div>
            )}
          </div>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-500"
            style={{ width: `${(connectedCount / totalCount) * 100}%` }}
          />
        </div>
      </Card>

      {/* Broker Connection Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {brokers.map((broker) => {
          const colorStyle = colorStyles[broker.color as keyof typeof colorStyles];
          const cardStyle = broker.connected && broker.valid 
            ? colorStyle.connected 
            : broker.status === 'expired' 
            ? colorStyle.expired 
            : broker.status === 'error'
            ? colorStyle.error
            : 'bg-gray-50 border-gray-200 text-gray-700';

          return (
            <Card 
              key={broker.id}
              className={`transition-all duration-200 ${cardStyle}`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center font-bold text-lg ${colorStyle.logo}`}>
                    {broker.name.charAt(0)}
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg">{broker.name}</h3>
                    <p className="text-sm opacity-80">
                      {broker.description}
                    </p>
                  </div>
                </div>
                
                <div className={`px-3 py-1 rounded text-xs font-semibold ${colorStyle.status}`}>
                  {broker.connected && broker.valid ? '✓ Connected' :
                   broker.status === 'expired' ? '⚠ Expired' :
                   broker.status === 'error' ? '✗ Error' : '○ Disconnected'}
                </div>
              </div>

              <div className="mb-4">
                <h4 className="font-medium mb-2">Features:</h4>
                <div className="flex flex-wrap gap-1">
                  {broker.features.map((feature, index) => (
                    <span 
                      key={index}
                      className="px-2 py-1 bg-white/50 rounded text-xs"
                    >
                      {feature}
                    </span>
                  ))}
                </div>
              </div>

              {broker.lastConnected && (
                <div className="mb-4 text-xs opacity-70">
                  Last connected: {new Date(broker.lastConnected).toLocaleString()}
                </div>
              )}

              <div className="flex gap-2">
                {broker.connected && broker.valid ? (
                  <>
                    <button
                      onClick={() => disconnectBroker(broker.id)}
                      className="flex-1 px-4 py-2 bg-red-100 text-red-800 rounded-lg hover:bg-red-200 transition-colors font-medium"
                    >
                      Disconnect
                    </button>
                    <button
                      onClick={() => fetchBrokerStatuses()}
                      className="px-4 py-2 bg-white/50 rounded-lg hover:bg-white/70 transition-colors"
                    >
                      Test
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => connectBroker(broker.id)}
                    disabled={connecting === broker.id}
                    className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                      connecting === broker.id
                        ? 'bg-gray-400 text-white cursor-not-allowed'
                        : colorStyle.button
                    }`}
                  >
                    {connecting === broker.id ? (
                      <span className="flex items-center justify-center gap-2">
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        Connecting...
                      </span>
                    ) : (
                      `Connect ${broker.name}`
                    )}
                  </button>
                )}
              </div>
            </Card>
          );
        })}
      </div>

      {/* API Benefits */}
      <Card title="Multi-Broker Benefits" className="mt-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
          <div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
              <span className="text-xl">🔄</span>
            </div>
            <h4 className="font-semibold mb-2">Redundancy</h4>
            <p className="text-gray-600 text-sm">
              Never miss market opportunities with automatic failover between brokers
            </p>
          </div>
          <div>
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-3">
              <span className="text-xl">⚡</span>
            </div>
            <h4 className="font-semibold mb-2">Performance</h4>
            <p className="text-gray-600 text-sm">
              Load balancing across multiple APIs for faster data and execution
            </p>
          </div>
          <div>
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-3">
              <span className="text-xl">🎯</span>
            </div>
            <h4 className="font-semibold mb-2">Best Execution</h4>
            <p className="text-gray-600 text-sm">
              Compare prices and execution quality across multiple brokers
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}