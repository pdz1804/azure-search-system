import React from 'react';
import { message } from 'antd';
import { 
  DocumentTextIcon,
  EyeIcon,
  HeartIcon,
  BookOpenIcon
} from '@heroicons/react/24/outline';
import { 
  DocumentTextIcon as DocumentSolid,
  EyeIcon as EyeSolid,
  HeartIcon as HeartSolid
} from '@heroicons/react/24/solid';
import { useAuthorStats } from '../hooks/useAuthorStats';
import { formatNumber } from '../utils/helpers';
import { motion } from 'framer-motion';

/**
 * Reusable dashboard statistics component
 * Shows personal writing statistics for a user
 */
const DashboardStats = ({ userId, className = "" }) => {
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

  const publishRate = stats?.total_articles > 0 
    ? Math.round((stats.published_articles / stats.total_articles) * 100) 
    : 0;

  const statCards = [
    {
      title: 'Total Articles',
      value: stats.total_articles || 0,
      icon: DocumentSolid,
      color: 'from-blue-500 to-indigo-600',
      bgColor: 'from-blue-50 to-indigo-50'
    },
    {
      title: 'Published',
      value: stats.published_articles || 0,
      icon: BookOpenIcon,
      color: 'from-green-500 to-emerald-600',
      bgColor: 'from-green-50 to-emerald-50'
    },
    {
      title: 'Total Views',
      value: formatNumber(stats.total_views || 0),
      icon: EyeSolid,
      color: 'from-purple-500 to-indigo-600',
      bgColor: 'from-purple-50 to-indigo-50'
    },
    {
      title: 'Total Likes',
      value: formatNumber(stats.total_likes || 0),
      icon: HeartSolid,
      color: 'from-pink-500 to-red-500',
      bgColor: 'from-pink-50 to-red-50'
    }
  ];

  return (
    <div className={className}>
      {/* Personal Writing Statistics Section */}
      <div className="bg-white rounded-3xl shadow-xl border border-slate-200 overflow-hidden mb-8">
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 px-8 py-6 border-b border-slate-200">
          <h2 className="text-2xl font-bold text-slate-900 flex items-center gap-3">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <DocumentTextIcon className="text-white text-lg" />
            </div>
            Writing Statistics
          </h2>
          <p className="text-slate-600 mt-2">
            Track your writing progress and engagement
          </p>
        </div>
        
        <div className="p-8">
          {/* Stats Grid */}
          <motion.div 
            className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            {statCards.map((card, index) => {
              const IconComponent = card.icon;
              return (
                <motion.div
                  key={card.title}
                  className={`bg-gradient-to-br ${card.bgColor} rounded-2xl shadow-lg border border-white/50 p-6 hover:shadow-xl transition-all duration-300`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.1 * index }}
                  whileHover={{ scale: 1.02 }}
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${card.color} flex items-center justify-center shadow-lg`}>
                      <IconComponent className="w-5 h-5 text-white" />
                    </div>
                  </div>
                  <div className="text-2xl font-bold text-gray-900 mb-1">
                    {card.value}
                  </div>
                  <div className="text-gray-600 text-sm font-medium">
                    {card.title}
                  </div>
                </motion.div>
              );
            })}
          </motion.div>

          {/* Additional Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-gradient-to-br from-gray-50 to-blue-50 rounded-xl p-6 border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Publish Rate</h3>
              <div className="text-3xl font-bold text-blue-600 mb-1">{publishRate}%</div>
              <p className="text-gray-600 text-sm">Articles published vs drafts</p>
            </div>
            
            <div className="bg-gradient-to-br from-gray-50 to-green-50 rounded-xl p-6 border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Avg Views</h3>
              <div className="text-3xl font-bold text-green-600 mb-1">{formatNumber(stats.avg_views)}</div>
              <p className="text-gray-600 text-sm">Average views per article</p>
            </div>
            
            <div className="bg-gradient-to-br from-gray-50 to-purple-50 rounded-xl p-6 border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Draft Articles</h3>
              <div className="text-3xl font-bold text-purple-600 mb-1">{stats.draft_articles}</div>
              <p className="text-gray-600 text-sm">Unpublished articles</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardStats;
