import React, { useState } from 'react';
import { 
  PlusOutlined, 
  FileTextOutlined,
  EditOutlined,
  EyeOutlined,
  HeartOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import ArticleList from '../components/ArticleList';
import { useAuth } from '../context/AuthContext';
import { useAuthorStats, invalidateAuthorStats } from '../hooks/useAuthorStats';
import { formatNumber } from '../utils/helpers';

const MyArticles = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('all');
  
  // Use shared hook for author stats to prevent duplicate API calls
  const { stats: authorStats, loading: statsLoading } = useAuthorStats(user?.id, { 
    enabled: !!user?.id,
    limit: 1000 
  });

  // Transform author stats to match component expectations
  const stats = {
    total: authorStats.total_articles || 0,
    published: authorStats.published_articles || 0,
    drafts: authorStats.draft_articles || 0,
    totalViews: authorStats.total_views || 0,
    totalLikes: authorStats.total_likes || 0
  };

  const handleCreateArticle = () => {
    navigate('/write');
  };

  const handleRefresh = () => {
    // Invalidate the cache to force a fresh fetch
    if (user?.id) {
      invalidateAuthorStats(user.id);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Hero Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
            <div>
              <h1 className="text-4xl font-bold flex items-center gap-3">
                <FileTextOutlined className="text-3xl" />
                My Articles
              </h1>
              <p className="text-blue-100 text-lg mt-2">Manage and track your published content</p>
            </div>
            <button 
              onClick={handleCreateArticle}
              className="bg-white text-blue-600 px-8 py-3 rounded-full font-semibold hover:shadow-lg transition-all duration-200 flex items-center gap-2 text-lg"
            >
              <PlusOutlined />
              Write New Article
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-12">
          <div className="bg-white rounded-2xl p-6 shadow-lg border border-slate-200 text-center">
            <div className="w-14 h-14 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <FileTextOutlined className="text-blue-600 text-2xl" />
            </div>
            <div className="text-3xl font-bold text-slate-900 mb-1">{stats.total}</div>
            <div className="text-slate-600 font-medium">Total Articles</div>
          </div>
          
          <div className="bg-white rounded-2xl p-6 shadow-lg border border-slate-200 text-center">
            <div className="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <EditOutlined className="text-green-600 text-2xl" />
            </div>
            <div className="text-3xl font-bold text-slate-900 mb-1">{stats.published}</div>
            <div className="text-slate-600 font-medium">Published</div>
          </div>
          
          <div className="bg-white rounded-2xl p-6 shadow-lg border border-slate-200 text-center">
            <div className="w-14 h-14 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <EyeOutlined className="text-purple-600 text-2xl" />
            </div>
            <div className="text-3xl font-bold text-slate-900 mb-1">{formatNumber(stats.totalViews)}</div>
            <div className="text-slate-600 font-medium">Total Views</div>
          </div>
          
          <div className="bg-white rounded-2xl p-6 shadow-lg border border-slate-200 text-center">
            <div className="w-14 h-14 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <HeartOutlined className="text-red-600 text-2xl" />
            </div>
            <div className="text-3xl font-bold text-slate-900 mb-1">{formatNumber(stats.totalLikes)}</div>
            <div className="text-slate-600 font-medium">Total Likes</div>
          </div>
        </div>

        {/* Articles Section */}
        <div className="bg-white rounded-2xl shadow-lg border border-slate-200 overflow-hidden">
          <div className="border-b border-slate-200">
            <div className="flex space-x-8 px-8 pt-6">
              <button 
                onClick={() => setActiveTab('all')}
                className={`pb-4 border-b-2 font-semibold transition-colors ${
                  activeTab === 'all' 
                    ? 'border-blue-600 text-blue-600' 
                    : 'border-transparent text-slate-600 hover:text-slate-900'
                }`}
              >
                All ({stats.total})
              </button>
              <button 
                onClick={() => setActiveTab('published')}
                className={`pb-4 border-b-2 font-semibold transition-colors ${
                  activeTab === 'published' 
                    ? 'border-green-600 text-green-600' 
                    : 'border-transparent text-slate-600 hover:text-slate-900'
                }`}
              >
                Published ({stats.published})
              </button>
              <button 
                onClick={() => setActiveTab('drafts')}
                className={`pb-4 border-b-2 font-semibold transition-colors ${
                  activeTab === 'drafts' 
                    ? 'border-yellow-600 text-yellow-600' 
                    : 'border-transparent text-slate-600 hover:text-slate-900'
                }`}
              >
                Drafts ({stats.drafts})
              </button>
            </div>
          </div>
          
          <div className="p-8">
            {activeTab === 'all' && (
              <ArticleList 
                key="all-articles"
                authorId={user?.id}
                showAuthor={false}
                onRefresh={handleRefresh}
                loadAll
              />
            )}
            {activeTab === 'published' && (
              <ArticleList 
                key="published-articles"
                authorId={user?.id}
                status="published"
                showAuthor={false}
                onRefresh={handleRefresh}
              />
            )}
            {activeTab === 'drafts' && (
              stats.drafts > 0 ? (
                <ArticleList 
                  key="draft-articles"
                  authorId={user?.id}
                  status="draft"
                  showAuthor={false}
                  onRefresh={handleRefresh}
                />
              ) : (
                <div className="text-center py-16">
                  <div className="w-24 h-24 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                    <FileTextOutlined className="text-4xl text-gray-400" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-600 mb-2">No drafts yet</h3>
                  <p className="text-gray-500">Your draft articles will appear here</p>
                </div>
              )
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MyArticles;
