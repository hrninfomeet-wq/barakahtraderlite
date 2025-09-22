"use client";

/**
 * F&O Strategy Guides - Barakah Trader Lite
 * Comprehensive strategy library with P&L analysis
 */

import { PageHeader } from '@/components/ui/page-header';
import { Card } from '@/components/ui/card';

const strategyCategories = [
  {
    name: 'Bullish Strategies',
    description: 'Profit from rising markets',
    strategies: [
      { name: 'Long Call', difficulty: 'Beginner', description: 'Buy call option for unlimited upside' },
      { name: 'Bull Call Spread', difficulty: 'Intermediate', description: 'Buy call, sell higher call' },
      { name: 'Bull Put Spread', difficulty: 'Intermediate', description: 'Sell put, buy lower put' },
    ],
    color: 'green'
  },
  {
    name: 'Bearish Strategies',
    description: 'Profit from falling markets',
    strategies: [
      { name: 'Long Put', difficulty: 'Beginner', description: 'Buy put option for downside protection' },
      { name: 'Bear Call Spread', difficulty: 'Intermediate', description: 'Sell call, buy higher call' },
      { name: 'Bear Put Spread', difficulty: 'Intermediate', description: 'Buy put, sell lower put' },
    ],
    color: 'red'
  },
  {
    name: 'Neutral Strategies',
    description: 'Profit from sideways markets',
    strategies: [
      { name: 'Iron Condor', difficulty: 'Advanced', description: 'Sell call/put spreads around current price' },
      { name: 'Butterfly Spread', difficulty: 'Advanced', description: 'Limited risk, limited profit strategy' },
      { name: 'Short Straddle', difficulty: 'Advanced', description: 'Sell call and put at same strike' },
    ],
    color: 'blue'
  },
  {
    name: 'Volatility Strategies',
    description: 'Profit from volatility changes',
    strategies: [
      { name: 'Long Straddle', difficulty: 'Intermediate', description: 'Buy call and put at same strike' },
      { name: 'Long Strangle', difficulty: 'Intermediate', description: 'Buy call and put at different strikes' },
      { name: 'Calendar Spread', difficulty: 'Advanced', description: 'Different expiration dates' },
    ],
    color: 'purple'
  },
];

const difficultyColors = {
  'Beginner': 'bg-green-100 text-green-800',
  'Intermediate': 'bg-yellow-100 text-yellow-800', 
  'Advanced': 'bg-red-100 text-red-800',
};

export default function StrategiesPage() {
  return (
    <div className="p-6 max-w-6xl mx-auto">
      <PageHeader 
        title="F&O Strategy Library"
        subtitle="Master proven strategies for every market condition with risk analysis and P&L visualization"
      >
        <a 
          href="/education"
          className="px-4 py-2 text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
        >
          ← Back to Learning Center
        </a>
      </PageHeader>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
        {strategyCategories.map((category) => (
          <Card 
            key={category.name}
            title={category.name}
            subtitle={category.description}
            className={`border-l-4 ${
              category.color === 'green' ? 'border-l-green-500' :
              category.color === 'red' ? 'border-l-red-500' :
              category.color === 'blue' ? 'border-l-blue-500' :
              'border-l-purple-500'
            }`}
          >
            <div className="space-y-3">
              {category.strategies.map((strategy) => (
                <div 
                  key={strategy.name}
                  className="p-3 border rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => {
                    // Navigate to strategy detail
                    const slug = strategy.name.toLowerCase().replace(/\s+/g, '-');
                    window.location.href = `/education/strategies/${slug}`;
                  }}
                >
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-medium text-gray-900">
                      {strategy.name}
                    </h4>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      difficultyColors[strategy.difficulty as keyof typeof difficultyColors]
                    }`}>
                      {strategy.difficulty}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">
                    {strategy.description}
                  </p>
                </div>
              ))}
            </div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <Card title="Strategy Builder" variant="interactive" className="lg:col-span-2">
          <div className="mb-4">
            <p className="text-gray-600 mb-4">
              Build and analyze custom multi-leg strategies with real-time P&L visualization. 
              Perfect for testing your strategy ideas before implementation.
            </p>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Features:</h4>
                <ul className="space-y-1 text-gray-600">
                  <li>• Multi-leg strategy construction</li>
                  <li>• Real-time P&L calculation</li>
                  <li>• Greeks analysis</li>
                  <li>• Risk metrics visualization</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Analysis:</h4>
                <ul className="space-y-1 text-gray-600">
                  <li>• Maximum profit/loss</li>
                  <li>• Breakeven points</li>
                  <li>• Probability of profit</li>
                  <li>• Time decay impact</li>
                </ul>
              </div>
            </div>
          </div>
          
          <button className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold">
            Launch Strategy Builder
          </button>
        </Card>

        <Card title="Market Outlook Guide">
          <div className="space-y-4 text-sm">
            <div>
              <h4 className="font-semibold text-gray-900 mb-2 flex items-center">
                <span className="w-3 h-3 bg-green-500 rounded-full mr-2"></span>
                Bullish Market
              </h4>
              <p className="text-gray-600">Rising prices, positive sentiment. Use call spreads, covered calls.</p>
            </div>
            
            <div>
              <h4 className="font-semibold text-gray-900 mb-2 flex items-center">
                <span className="w-3 h-3 bg-red-500 rounded-full mr-2"></span>
                Bearish Market
              </h4>
              <p className="text-gray-600">Falling prices, negative sentiment. Use put spreads, protective puts.</p>
            </div>
            
            <div>
              <h4 className="font-semibold text-gray-900 mb-2 flex items-center">
                <span className="w-3 h-3 bg-blue-500 rounded-full mr-2"></span>
                Neutral Market
              </h4>
              <p className="text-gray-600">Sideways movement. Use iron condors, butterfly spreads.</p>
            </div>
            
            <div>
              <h4 className="font-semibold text-gray-900 mb-2 flex items-center">
                <span className="w-3 h-3 bg-purple-500 rounded-full mr-2"></span>
                High Volatility
              </h4>
              <p className="text-gray-600">Increased price swings. Use long straddles, strangles.</p>
            </div>
          </div>
        </Card>
      </div>

      <Card title="Strategy Performance Tracker" className="mb-6">
        <div className="text-center py-8">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">📊</span>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Track Your Strategy Performance
          </h3>
          <p className="text-gray-600 mb-6 max-w-2xl mx-auto">
            Monitor the performance of your paper trading strategies with detailed analytics, 
            win rates, and risk-adjusted returns. Connect with live market data for real-time tracking.
          </p>
          <div className="flex justify-center gap-4">
            <button className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
              View Performance
            </button>
            <button className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
              Learn More
            </button>
          </div>
        </div>
      </Card>
    </div>
  );
}