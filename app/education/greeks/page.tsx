"use client";

/**
 * Greeks Overview - Barakah Trader Lite
 * Overview of all Greeks with navigation to individual calculators
 */

import { PageHeader } from '@/components/ui/page-header';
import { Card } from '@/components/ui/card';

const greeksData = [
  {
    symbol: 'Δ',
    name: 'Delta',
    slug: 'delta',
    description: 'Measures price sensitivity to underlying asset price changes',
    color: 'blue',
    importance: 'Critical for hedging and directional strategies',
  },
  {
    symbol: 'Γ',
    name: 'Gamma',
    slug: 'gamma',
    description: 'Measures the rate of change of Delta',
    color: 'green',
    importance: 'Important for managing Delta risk over time',
  },
  {
    symbol: 'Θ',
    name: 'Theta',
    slug: 'theta',
    description: 'Measures time decay effect on option price',
    color: 'red',
    importance: 'Critical for time-based strategies',
  },
  {
    symbol: 'ν',
    name: 'Vega',
    slug: 'vega',
    description: 'Measures sensitivity to implied volatility changes',
    color: 'purple',
    importance: 'Key for volatility-based trading strategies',
  },
  {
    symbol: 'ρ',
    name: 'Rho',
    slug: 'rho',
    description: 'Measures sensitivity to interest rate changes',
    color: 'orange',
    importance: 'Relevant for long-term options and high rates',
  },
];

const colorStyles = {
  blue: 'bg-blue-600 text-white border-blue-200 hover:border-blue-300',
  green: 'bg-green-600 text-white border-green-200 hover:border-green-300',
  red: 'bg-red-600 text-white border-red-200 hover:border-red-300',
  purple: 'bg-purple-600 text-white border-purple-200 hover:border-purple-300',
  orange: 'bg-orange-600 text-white border-orange-200 hover:border-orange-300',
};

export default function GreeksOverviewPage() {
  return (
    <div className="p-6 max-w-6xl mx-auto">
      <PageHeader
        title="Options Greeks"
        subtitle="Master the mathematical foundations of options pricing and risk management"
      >
        <a
          href="/education"
          className="px-4 py-2 text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
        >
          ← Back to Learning Center
        </a>
      </PageHeader>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {greeksData.map((greek) => (
          <Card
            key={greek.slug}
            variant="interactive"
            className="relative overflow-hidden"
            onClick={() => {
              // Navigate to individual Greek page
              window.location.href = `/education/greeks/${greek.slug}`;
            }}
          >
            <div className="flex items-start justify-between mb-4">
              <div className={`
                w-12 h-12 rounded-full flex items-center justify-center text-xl font-bold
                ${colorStyles[greek.color as keyof typeof colorStyles]}
              `}>
                {greek.symbol}
              </div>
              <div className="text-right">
                <h3 className="text-lg font-bold text-gray-900">
                  {greek.name}
                </h3>
              </div>
            </div>

            <p className="text-gray-600 mb-3 text-sm">
              {greek.description}
            </p>

            <div className="mt-4 pt-3 border-t border-gray-100">
              <p className="text-xs text-gray-500 font-medium">
                Why it matters:
              </p>
              <p className="text-xs text-gray-600">
                {greek.importance}
              </p>
            </div>

            <div className="absolute top-2 right-2">
              <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600 text-xs">→</span>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <Card title="Interactive Greeks Calculator" className="mb-6">
        <div className="flex flex-col md:flex-row items-start justify-between gap-4">
          <div className="flex-1">
            <p className="text-gray-600 mb-4">
              Use our interactive calculator to see how Greeks change with different market conditions.
              Input your option parameters and watch the Greeks update in real-time.
            </p>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Real-time calculation using Black-Scholes model</li>
              <li>• Visual charts showing Greeks sensitivity</li>
              <li>• Compare multiple scenarios side-by-side</li>
              <li>• Export calculations for your records</li>
            </ul>
          </div>
          <button
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold whitespace-nowrap"
            onClick={() => {
              // Navigate to calculator (implement later)
              console.log('Navigate to Greeks calculator');
            }}
          >
            Launch Calculator
          </button>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Learning Path" variant="success">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-6 h-6 bg-green-600 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-bold">1</span>
              </div>
              <span className="text-sm">Start with Delta - understand directional risk</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-6 h-6 bg-green-600 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-bold">2</span>
              </div>
              <span className="text-sm">Learn Gamma - manage Delta changes</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-6 h-6 bg-green-600 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-bold">3</span>
              </div>
              <span className="text-sm">Master Theta - time decay strategies</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-6 h-6 bg-gray-300 rounded-full flex items-center justify-center">
                <span className="text-gray-600 text-xs font-bold">4</span>
              </div>
              <span className="text-sm text-gray-500">Advanced: Vega and Rho</span>
            </div>
          </div>
        </Card>

        <Card title="Pro Tips" variant="warning">
          <div className="space-y-2 text-sm text-gray-700">
            <p><strong>💡 Focus on Delta first:</strong> It's the most important Greek for beginners</p>
            <p><strong>⚡ Gamma accelerates:</strong> High Gamma means Delta changes quickly</p>
            <p><strong>⏰ Theta never stops:</strong> Time decay affects all options constantly</p>
            <p><strong>🌊 Vega in volatile markets:</strong> Critical during earnings or events</p>
          </div>
        </Card>
      </div>
    </div>
  );
}