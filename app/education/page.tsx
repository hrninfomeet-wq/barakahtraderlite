"use client";

/**
 * Education Dashboard - Barakah Trader Lite
 * Main educational hub with learning paths and progress tracking
 */

import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/ui/page-header';
import { Card } from '@/components/ui/card';
import { Loader } from '@/components/ui/loader';
import { ErrorState } from '@/components/ui/error-state';
import { educationApi, type LearningPath } from '@/lib/api-client';

export default function EducationPage() {
  const [learningPath, setLearningPath] = useState<LearningPath | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLearningPath = async () => {
    setLoading(true);
    setError(null);
    
    const response = await educationApi.getLearningPath();
    if (response.success && response.data) {
      setLearningPath(response.data);
    } else {
      setError(response.error || 'Failed to load learning path');
    }
    
    setLoading(false);
  };

  useEffect(() => {
    fetchLearningPath();
  }, []);

  if (loading) {
    return (
      <div className="p-6 max-w-6xl mx-auto">
        <PageHeader title="F&O Learning Center" />
        <Loader message="Loading your learning path..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 max-w-6xl mx-auto">
        <PageHeader title="F&O Learning Center" />
        <ErrorState 
          message={error} 
          retry={fetchLearningPath}
        />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <PageHeader 
        title="F&O Learning Center"
        subtitle="Master Futures & Options trading with interactive tutorials and real market examples"
      />

      {learningPath && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Progress Overview */}
          <div className="lg:col-span-2">
            <Card title="Your Learning Journey" className="mb-6">
              <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-600">
                    Overall Progress
                  </span>
                  <span className="text-sm font-bold text-blue-600">
                    {learningPath.progress_percentage}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${learningPath.progress_percentage}%` }}
                  />
                </div>
              </div>
              <p className="text-gray-600">
                {learningPath.completed_modules} of {learningPath.total_modules} modules completed
              </p>
            </Card>

            {/* Learning Modules */}
            <div className="space-y-4">
              <h2 className="text-xl font-semibold mb-4">Learning Modules</h2>
              {learningPath.modules.map((module, index) => (
                <Card 
                  key={module.id}
                  variant={module.is_completed ? 'success' : 'interactive'}
                  className="relative"
                  onClick={() => {
                    // Navigate to module (implement later)
                    console.log('Navigate to module:', module.id);
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className={`
                        w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold
                        ${module.is_completed 
                          ? 'bg-green-600 text-white' 
                          : 'bg-blue-100 text-blue-600'
                        }
                      `}>
                        {module.is_completed ? '✓' : index + 1}
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">
                          {module.name}
                        </h3>
                        <p className="text-gray-600 text-sm">
                          {module.description}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`
                        px-3 py-1 rounded text-xs font-medium
                        ${module.type === 'tutorial' ? 'bg-blue-100 text-blue-800' : ''}
                        ${module.type === 'interactive' ? 'bg-purple-100 text-purple-800' : ''}
                        ${module.type === 'assessment' ? 'bg-orange-100 text-orange-800' : ''}
                      `}>
                        {module.type}
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        ~{module.estimated_time_minutes} min
                      </p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>

          {/* Quick Access Sidebar */}
          <div className="space-y-6">
            <Card title="Quick Access">
              <div className="space-y-3">
                <a 
                  href="/education/greeks" 
                  className="flex items-center p-3 rounded-lg bg-blue-50 hover:bg-blue-100 transition-colors"
                >
                  <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center mr-3">
                    <span className="text-white text-sm font-bold">Δ</span>
                  </div>
                  <div>
                    <p className="font-medium">Greeks Calculator</p>
                    <p className="text-xs text-gray-600">Interactive options pricing</p>
                  </div>
                </a>
                
                <a 
                  href="/education/strategies" 
                  className="flex items-center p-3 rounded-lg bg-green-50 hover:bg-green-100 transition-colors"
                >
                  <div className="w-8 h-8 bg-green-600 rounded-lg flex items-center justify-center mr-3">
                    <span className="text-white text-sm font-bold">📈</span>
                  </div>
                  <div>
                    <p className="font-medium">Strategy Guides</p>
                    <p className="text-xs text-gray-600">F&O trading strategies</p>
                  </div>
                </a>
                
                <a 
                  href="/education/progress" 
                  className="flex items-center p-3 rounded-lg bg-purple-50 hover:bg-purple-100 transition-colors"
                >
                  <div className="w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center mr-3">
                    <span className="text-white text-sm font-bold">🎯</span>
                  </div>
                  <div>
                    <p className="font-medium">Progress Tracking</p>
                    <p className="text-xs text-gray-600">Your learning stats</p>
                  </div>
                </a>
              </div>
            </Card>

            <Card title="Getting Started" variant="warning">
              <p className="text-sm text-gray-700 mb-3">
                New to F&O trading? Start with our beginner-friendly modules to build a solid foundation.
              </p>
              <div className="text-xs text-gray-600 space-y-1">
                <p>• Learn options basics</p>
                <p>• Understand Greeks</p>
                <p>• Practice with paper trading</p>
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}