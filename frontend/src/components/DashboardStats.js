import React from 'react';
import { message } from 'antd';
import { useNavigate } from 'react-router-dom';
import { 
  DocumentTextIcon,
  EyeIcon,
  HeartIcon,
  BookOpenIcon,
  ArrowTrendingUpIcon
} from '@heroicons/react/24/outline';
import { 
  DocumentTextIcon as DocumentSolid,
  EyeIcon as EyeSolid,
  HeartIcon as HeartSolid,
  BookOpenIcon as BookOpenSolid
} from '@heroicons/react/24/solid';
import { useAuthorStats } from '../hooks/useAuthorStats';
import { formatNumber } from '../utils/helpers';
import { motion } from 'framer-motion';

/**
 * Clean, robust dashboard statistics component
 * Shows personal writing statistics with improved organization and no redundancy
 */
const DashboardStats = ({ userId, className = "" }) => {
  const navigate = useNavigate();
  const { stats, loading, error } = useAuthorStats(userId, { 
    enabled: !!userId,
    limit: 1000 
  });

  // Show error message if there's an error
  if (error) {
    message.error('Failed to load statistics');
    console.error('Error fetching stats:', error);
  }

  if (loading) {
    return (
      <div className={`${className} flex items-center justify-center p-8`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-2"></div>
          <p className="text-gray-600 text-sm">Loading statistics...</p>
        </div>
      </div>
    );
  }

  // Calculate derived statistics
  const publishRate = stats?.total_articles > 0 
    ? Math.round((stats.published_articles / stats.total_articles) * 100) 
    : 0;
  
  const avgViews = stats?.total_articles > 0 
    ? Math.round((stats.total_views / stats.total_articles)) 
    : 0;
  
  const avgLikes = stats?.total_articles > 0 
    ? Math.round((stats.total_likes / stats.total_articles)) 
    : 0;

  // Primary metrics - most important stats
  const primaryMetrics = [
    {
      title: 'Total Articles',
      value: stats.total_articles || 0,
      icon: DocumentSolid,
      color: 'from-blue-500 to-indigo-600',
      bgColor: 'from-blue-50 to-indigo-50',
      description: 'All articles created'
    },
    {
      title: 'Published',
      value: stats.published_articles || 0,
      icon: BookOpenSolid,
      color: 'from-green-500 to-emerald-600',
      bgColor: 'from-green-50 to-emerald-50',
      description: 'Live articles'
    },
    {
      title: 'Total Views',
      value: formatNumber(stats.total_views || 0),
      icon: EyeSolid,
      color: 'from-purple-500 to-indigo-600',
      bgColor: 'from-purple-50 to-indigo-50',
      description: 'Article engagement'
    },
    {
      title: 'Total Likes',
      value: formatNumber(stats.total_likes || 0),
      icon: HeartSolid,
      color: 'from-pink-500 to-red-500',
      bgColor: 'from-pink-50 to-red-50',
      description: 'Reader appreciation'
    }
  ];

  // Secondary metrics - insights and ratios
  const secondaryMetrics = [
    {
      title: 'Publish Rate',
      value: `${publishRate}%`,
      icon: ArrowTrendingUpIcon,
      color: 'from-blue-500 to-cyan-500',
      bgColor: 'from-blue-50 to-cyan-50',
      description: 'Published vs drafts'
    },
    {
      title: 'Avg Views',
      value: formatNumber(avgViews),
      icon: EyeIcon,
      color: 'from-emerald-500 to-green-500',
      bgColor: 'from-emerald-50 to-green-50',
      description: 'Per article average'
    },
    {
      title: 'Avg Likes',
      value: formatNumber(avgLikes),
      icon: HeartIcon,
      color: 'from-rose-500 to-pink-500',
      bgColor: 'from-rose-50 to-pink-50',
      description: 'Per article average'
    }
  ];

  return (
    <div className={className}>
      {/* Writing Statistics Dashboard */}
              <div className="bg-white rounded-3xl shadow-xl border border-slate-200 overflow-hidden mb-8">
          {/* Header */}
          <div className="bg-gradient-to-r from-indigo-50 to-purple-50 px-4 sm:px-6 lg:px-8 py-4 sm:py-6 border-b border-slate-200">
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 flex items-center gap-3">
              <div className="w-6 h-6 sm:w-8 sm:h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
                <DocumentTextIcon className="text-white text-sm sm:text-lg" />
              </div>
              Writing Statistics
            </h2>
            <p className="text-slate-600 mt-2 text-sm sm:text-base">
              Track your writing progress and reader engagement
            </p>
          </div>
        
        <div className="p-4 sm:p-6 lg:p-8">
          {/* Primary Metrics Grid - Most Important Stats */}
          {/* <div className="mb-6 sm:mb-8">
            <h3 className="text-base sm:text-lg font-semibold text-slate-700 mb-3 sm:mb-4 flex items-center gap-2">
              <div className="w-3 h-3 sm:w-4 sm:h-4 bg-indigo-500 rounded-full"></div>
              Key Metrics
            </h3>
            <motion.div 
              className="grid grid-cols-2 lg:grid-cols-4 gap-6"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              {primaryMetrics.map((card, index) => {
                const IconComponent = card.icon;
                return (
                  <motion.div
                    key={card.title}
                    className={`bg-gradient-to-br ${card.bgColor} rounded-2xl shadow-lg border border-white/50 p-6 hover:shadow-xl transition-all duration-300 group`}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.1 * index }}
                    whileHover={{ scale: 1.02 }}
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${card.color} flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-200`}>
                        <IconComponent className="w-5 h-5 text-white" />
                      </div>
                    </div>
                    <div className="text-3xl font-bold text-gray-900 mb-2">
                      {card.value}
                    </div>
                    <div className="text-gray-700 font-medium mb-1">
                      {card.title}
                    </div>
                    <div className="text-gray-500 text-xs">
                      {card.description}
                    </div>
                  </motion.div>
                );
              })}
            </motion.div>
          </div> */}

          {/* Secondary Metrics - Insights and Ratios */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-slate-700 mb-4 flex items-center gap-2">
              <div className="w-4 h-4 bg-emerald-500 rounded-full"></div>
              Performance Insights
            </h3>
            <motion.div 
              className="grid grid-cols-1 md:grid-cols-3 gap-6"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
            >
              {secondaryMetrics.map((metric, index) => {
                const IconComponent = metric.icon;
                return (
                  <motion.div
                    key={metric.title}
                    className={`bg-gradient-to-br ${metric.bgColor} rounded-xl p-6 border border-gray-200 hover:shadow-lg transition-all duration-300`}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.5 + (0.1 * index) }}
                    whileHover={{ scale: 1.01 }}
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${metric.color} flex items-center justify-center`}>
                        <IconComponent className="w-4 h-4 text-white" />
                      </div>
                      <h4 className="text-lg font-semibold text-gray-900">{metric.title}</h4>
                    </div>
                    <div className="text-2xl font-bold text-gray-800 mb-2">{metric.value}</div>
                    <p className="text-gray-600 text-sm">{metric.description}</p>
                  </motion.div>
                );
              })}
            </motion.div>
          </div>

          {/* Quick Actions */}
          <motion.div 
            className="bg-gradient-to-r from-slate-50 to-gray-50 rounded-xl p-6 border border-slate-200"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
          >
            <h3 className="text-lg font-semibold text-slate-700 mb-4 flex items-center gap-2">
              <div className="w-4 h-4 bg-purple-500 rounded-full"></div>
              Quick Actions
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button 
                onClick={() => navigate('/write')}
                className="flex items-center gap-3 p-3 bg-white rounded-lg border border-slate-200 hover:border-indigo-300 hover:shadow-md transition-all duration-200 text-left w-full"
              >
                <div className="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center">
                  <DocumentTextIcon className="w-4 h-4 text-indigo-600" />
                </div>
                <div>
                  <div className="font-medium text-slate-700">Create Article</div>
                  <div className="text-xs text-slate-500">Start writing</div>
                </div>
              </button>
              <button 
                onClick={() => navigate('/my-articles?tab=drafts')}
                className="flex items-center gap-3 p-3 bg-white rounded-lg border border-slate-200 hover:border-emerald-300 hover:shadow-md transition-all duration-200 text-left w-full"
              >
                <div className="w-8 h-8 bg-emerald-100 rounded-lg flex items-center justify-center">
                  <BookOpenIcon className="w-4 h-4 text-emerald-600" />
                </div>
                <div>
                  <div className="font-medium text-slate-700">Publish Draft</div>
                  <div className="text-xs text-slate-500">Make it live</div>
                </div>
              </button>
              <button 
                onClick={() => navigate('/my-articles?tab=analytics')}
                className="flex items-center gap-3 p-3 bg-white rounded-lg border border-slate-200 hover:border-purple-300 hover:shadow-md transition-all duration-200 text-left w-full"
              >
                <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                  <ArrowTrendingUpIcon className="w-4 h-4 text-purple-600" />
                </div>
                <div>
                  <div className="font-medium text-slate-700">View Analytics</div>
                  <div className="text-xs text-slate-500">Track performance</div>
                </div>
              </button>
            </div>
          </motion.div>

          {/* Data Validation Section - For debugging */}
          {process.env.NODE_ENV === 'development' && (
            <motion.div 
              className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.7 }}
            >
              <h4 className="text-sm font-semibold text-yellow-800 mb-2 flex items-center gap-2">
                <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                Debug Info (Development Only)
              </h4>
              <div className="text-xs text-yellow-700 space-y-1">
                <div>Raw stats data: {JSON.stringify(stats, null, 2)}</div>
                <div>User ID: {userId}</div>
                <div>Cache status: {loading ? 'Loading...' : 'Loaded'}</div>
                {error && <div>Error: {error.message}</div>}
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DashboardStats;
