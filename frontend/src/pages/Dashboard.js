import React, { useState, useEffect } from 'react';
import { message } from 'antd';
import { 
  DocumentTextIcon,
  EyeIcon,
  HeartIcon,
  UserIcon,
  ChartBarIcon,
  PencilIcon,
  BookOpenIcon
} from '@heroicons/react/24/outline';
import { 
  DocumentTextIcon as DocumentSolid,
  EyeIcon as EyeSolid,
  HeartIcon as HeartSolid,
  UserIcon as UserSolid
} from '@heroicons/react/24/solid';
import { articleApi } from '../api/articleApi';
import { useAuth } from '../context/AuthContext';
import { formatNumber } from '../utils/helpers';
import { motion } from 'framer-motion';

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    total_articles: 0,
    published_articles: 0,
    draft_articles: 0,
    total_views: 0,
    total_likes: 0,
    avg_views: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      // Fetch global stats for admin or personal stats for writers
      if (user?.id) {
        // Fetch personal stats
        const response = await articleApi.getArticlesByAuthor(user.id, 1, 1000);
        if (response.success) {
          const articles = response.data?.items || response.items || [];
          
          const personalStats = {
            total_articles: articles.length,
            published_articles: articles.filter(a => a.status === 'published').length,
            draft_articles: articles.filter(a => a.status === 'draft').length,
            total_views: articles.reduce((sum, a) => sum + (a.views || 0), 0),
            total_likes: articles.reduce((sum, a) => sum + (a.likes || 0), 0),
            avg_views: articles.length > 0 ? Math.round(articles.reduce((sum, a) => sum + (a.views || 0), 0) / articles.length) : 0
          };
          
          setStats(personalStats);
        }
      }
    } catch (error) {
      message.error('Failed to load statistics');
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  const isAdmin = user?.role === 'admin';
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
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50">
      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Header */}
        <motion.div 
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h1 className="text-5xl font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent mb-4">
            Dashboard
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            {user?.role === 'admin' ? 'Global system overview and analytics' : 'Your personal writing statistics and achievements'}
          </p>
        </motion.div>

        {/* Stats Cards */}
        <motion.div 
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          {statCards.map((card, index) => {
            const IconComponent = card.icon;
            return (
              <motion.div
                key={card.title}
                className={`bg-gradient-to-br ${card.bgColor} rounded-2xl shadow-lg border border-white/50 p-8 hover:shadow-xl transition-all duration-300`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 * index }}
                whileHover={{ scale: 1.02 }}
              >
                <div className="flex items-center justify-between mb-4">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${card.color} flex items-center justify-center shadow-lg`}>
                    <IconComponent className="w-6 h-6 text-white" />
                  </div>
                </div>
                <h3 className="text-gray-600 text-sm font-medium mb-2">{card.title}</h3>
                <p className="text-3xl font-bold text-gray-900">{card.value}</p>
              </motion.div>
            );
          })}
        </motion.div>

        {/* Charts and Analytics */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Publication Rate */}
          <motion.div
            className="bg-white rounded-2xl shadow-lg border border-gray-100 p-8"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <h3 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
              <ChartBarIcon className="w-6 h-6 mr-3 text-indigo-600" />
              Publication Rate
            </h3>
            <div className="flex items-center justify-center">
              <div className="relative w-32 h-32">
                <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 120 120">
                  <circle
                    cx="60"
                    cy="60"
                    r="50"
                    fill="none"
                    stroke="#e5e7eb"
                    strokeWidth="8"
                  />
                  <circle
                    cx="60"
                    cy="60"
                    r="50"
                    fill="none"
                    stroke="url(#gradient)"
                    strokeWidth="8"
                    strokeDasharray={`${publishRate * 3.14} 314`}
                    strokeLinecap="round"
                  />
                  <defs>
                    <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#10b981" />
                      <stop offset="100%" stopColor="#059669" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-2xl font-bold text-gray-900">{publishRate}%</span>
                </div>
              </div>
            </div>
            <div className="text-center mt-6">
              <p className="text-gray-600">
                <span className="font-semibold text-green-600">{stats?.published_articles || 0}</span> published out of{' '}
                <span className="font-semibold text-gray-900">{stats?.total_articles || 0}</span> total articles
              </p>
            </div>
          </motion.div>

          {/* Performance Metrics */}
          <motion.div
            className="bg-white rounded-2xl shadow-lg border border-gray-100 p-8"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <h3 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
              <PencilIcon className="w-6 h-6 mr-3 text-purple-600" />
              Performance
            </h3>
            <div className="space-y-6">
              <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl p-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-600 font-medium">Avg Views/Article</span>
                  <EyeIcon className="w-5 h-5 text-purple-600" />
                </div>
                <p className="text-2xl font-bold text-gray-900">{stats?.avg_views || 0}</p>
              </div>
              <div className="bg-gradient-to-r from-pink-50 to-red-50 rounded-xl p-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-600 font-medium">Engagement Rate</span>
                  <HeartIcon className="w-5 h-5 text-pink-600" />
                </div>
                <p className="text-2xl font-bold text-gray-900">
                  {stats?.total_views > 0 ? ((stats.total_likes / stats.total_views) * 100).toFixed(2) : 0}%
                </p>
              </div>
              {isAdmin && (
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-gray-600 font-medium">Draft Articles</span>
                    <DocumentTextIcon className="w-5 h-5 text-blue-600" />
                  </div>
                  <p className="text-2xl font-bold text-gray-900">{stats?.draft_articles || 0}</p>
                </div>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
