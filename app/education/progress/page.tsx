"use client";

/**
 * Learning Progress - Barakah Trader Lite
 * Track learning progress, achievements, and certifications
 */

import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/ui/page-header';
import { Card } from '@/components/ui/card';
import { Loader } from '@/components/ui/loader';
import { ErrorState } from '@/components/ui/error-state';
import { educationApi } from '@/lib/api-client';

export default function ProgressPage() {
  const [progressData, setProgressData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProgress = async () => {
    setLoading(true);
    setError(null);
    
    const response = await educationApi.getProgress();
    if (response.success && response.data) {
      setProgressData(response.data);
    } else {
      setError(response.error || 'Failed to load progress data');
    }
    
    setLoading(false);
  };

  useEffect(() => {
    fetchProgress();
  }, []);

  if (loading) {
    return (
      <div className="p-6 max-w-6xl mx-auto">
        <PageHeader title="Learning Progress" />
        <Loader message="Loading your progress..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 max-w-6xl mx-auto">
        <PageHeader title="Learning Progress" />
        <ErrorState 
          message={error} 
          retry={fetchProgress}
        />
      </div>
    );
  }

  // Mock data structure for demonstration
  const mockProgress = {
    overall_progress: 65,
    modules_completed: 8,
    total_modules: 12,
    time_spent_minutes: 340,
    streak_days: 7,
    achievements: [
      { name: 'First Steps', description: 'Completed your first module', earned: true, date: '2024-01-15' },
      { name: 'Greeks Master', description: 'Mastered all Greeks concepts', earned: true, date: '2024-01-20' },
      { name: 'Strategy Explorer', description: 'Learned 5 different strategies', earned: false, progress: 60 },
      { name: 'Paper Trader', description: 'Placed 10 successful paper trades', earned: false, progress: 30 },
    ],
    recent_activities: [
      { type: 'module_complete', title: 'Completed Delta Tutorial', date: '2024-01-22' },
      { type: 'assessment_pass', title: 'Passed Greeks Assessment', score: 85, date: '2024-01-21' },
      { type: 'strategy_learn', title: 'Learned Bull Call Spread', date: '2024-01-20' },
    ],
    skill_levels: {
      'Options Basics': 90,
      'Greeks Understanding': 85,
      'Strategy Knowledge': 60,
      'Risk Management': 45,
      'Technical Analysis': 30,
    }
  };

  const data = progressData || mockProgress;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <PageHeader 
        title="Learning Progress"
        subtitle="Track your journey to becoming an F&O trading expert"
      >
        <a 
          href="/education"
          className="px-4 py-2 text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
        >
          ← Back to Learning Center
        </a>
      </PageHeader>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Overall Progress */}
        <Card title="Overall Progress">
          <div className="text-center">
            <div className="relative w-24 h-24 mx-auto mb-4">
              <svg className="w-24 h-24 transform -rotate-90">
                <circle 
                  cx="48" cy="48" r="40" 
                  fill="none" 
                  stroke="#e5e7eb" 
                  strokeWidth="8"
                />
                <circle 
                  cx="48" cy="48" r="40" 
                  fill="none" 
                  stroke="#3b82f6" 
                  strokeWidth="8"
                  strokeDasharray={`${2 * Math.PI * 40}`}
                  strokeDashoffset={`${2 * Math.PI * 40 * (1 - data.overall_progress / 100)}`}
                  className="transition-all duration-1000"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-2xl font-bold text-blue-600">
                  {data.overall_progress}%
                </span>
              </div>
            </div>
            <p className="text-gray-600">
              {data.modules_completed} of {data.total_modules} modules completed
            </p>
          </div>
        </Card>

        {/* Study Stats */}
        <Card title="Study Statistics">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Time Spent</span>
              <span className="font-semibold">
                {Math.floor(data.time_spent_minutes / 60)}h {data.time_spent_minutes % 60}m
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Current Streak</span>
              <span className="font-semibold text-orange-600">
                {data.streak_days} days 🔥
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Avg. Daily Study</span>
              <span className="font-semibold">
                {Math.round(data.time_spent_minutes / 7)} min/day
              </span>
            </div>
          </div>
        </Card>

        {/* Next Steps */}
        <Card title="Next Steps" variant="interactive">
          <div className="space-y-3">
            <div className="p-3 bg-blue-50 rounded-lg">
              <h4 className="font-semibold text-blue-900 mb-1">
                Continue Learning
              </h4>
              <p className="text-blue-700 text-sm">
                Complete Gamma tutorial to unlock advanced strategies
              </p>
            </div>
            <div className="p-3 bg-green-50 rounded-lg">
              <h4 className="font-semibold text-green-900 mb-1">
                Practice Trading
              </h4>
              <p className="text-green-700 text-sm">
                Try paper trading with Bull Call Spread strategy
              </p>
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Skill Levels */}
        <Card title="Skill Levels">
          <div className="space-y-4">
            {Object.entries(data.skill_levels).map(([skill, level]: [string, number]) => (
              <div key={skill}>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm font-medium text-gray-700">{skill}</span>
                  <span className="text-sm text-gray-500">{level}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-1000"
                    style={{ width: `${level}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Achievements */}
        <Card title="Achievements">
          <div className="space-y-3">
            {data.achievements.map((achievement: any, index: number) => (
              <div 
                key={index}
                className={`p-3 rounded-lg border ${
                  achievement.earned 
                    ? 'bg-green-50 border-green-200' 
                    : 'bg-gray-50 border-gray-200'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className={`font-semibold mb-1 ${
                      achievement.earned ? 'text-green-900' : 'text-gray-700'
                    }`}>
                      {achievement.earned ? '🏆' : '🔒'} {achievement.name}
                    </h4>
                    <p className={`text-sm ${
                      achievement.earned ? 'text-green-700' : 'text-gray-600'
                    }`}>
                      {achievement.description}
                    </p>
                    {achievement.earned ? (
                      <p className="text-xs text-green-600 mt-1">
                        Earned on {new Date(achievement.date).toLocaleDateString()}
                      </p>
                    ) : (
                      <div className="mt-2">
                        <div className="w-full bg-gray-200 rounded-full h-1">
                          <div 
                            className="bg-blue-600 h-1 rounded-full"
                            style={{ width: `${achievement.progress}%` }}
                          />
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                          {achievement.progress}% complete
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card title="Recent Activity">
        <div className="space-y-3">
          {data.recent_activities.map((activity: any, index: number) => (
            <div key={index} className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
              <div className={`w-2 h-2 rounded-full ${
                activity.type === 'module_complete' ? 'bg-green-500' :
                activity.type === 'assessment_pass' ? 'bg-blue-500' :
                'bg-purple-500'
              }`} />
              <div className="flex-1">
                <p className="font-medium text-gray-900">
                  {activity.title}
                </p>
                {activity.score && (
                  <p className="text-sm text-gray-600">
                    Score: {activity.score}%
                  </p>
                )}
              </div>
              <span className="text-sm text-gray-500">
                {new Date(activity.date).toLocaleDateString()}
              </span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}