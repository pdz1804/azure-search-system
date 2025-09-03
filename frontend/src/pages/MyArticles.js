import React, { useState, useEffect } from 'react';
import { 
  PlusOutlined, 
  FileTextOutlined,
  EditOutlined,
  EyeOutlined,
  HeartOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button, Tabs, message, Modal } from 'antd';
import ArticleList from '../components/ArticleList';
import { useAuth } from '../context/AuthContext';
import { useAuthorStats, invalidateAuthorStats } from '../hooks/useAuthorStats';
import { formatNumber } from '../utils/helpers';
import { articleApi } from '../api/articleApi';

const MyArticles = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('all');
  const [publishModalVisible, setPublishModalVisible] = useState(false);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [publishing, setPublishing] = useState(false);
  
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

  // Set initial tab based on URL query parameter
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const tab = searchParams.get('tab');
    if (tab && ['all', 'published', 'drafts', 'analytics'].includes(tab)) {
      setActiveTab(tab);
    }
  }, [location.search]);

  const handleCreateArticle = () => {
    navigate('/write');
  };

  const handleRefresh = () => {
    // Invalidate the cache to force a fresh fetch
    if (user?.id) {
      invalidateAuthorStats(user.id);
    }
  };

  const handlePublishDraft = async (article) => {
    setSelectedArticle(article);
    setPublishModalVisible(true);
  };

  const confirmPublish = async () => {
    if (!selectedArticle) return;
    
    setPublishing(true);
    try {
      await articleApi.updateArticle(selectedArticle.id, {
        status: 'published'
      });
      
      message.success('Article published successfully!');
      setPublishModalVisible(false);
      setSelectedArticle(null);
      
      // Refresh stats
      if (user?.id) {
        invalidateAuthorStats(user.id);
      }
    } catch (error) {
      message.error('Failed to publish article');
      console.error('Publish error:', error);
    } finally {
      setPublishing(false);
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
              <ClockCircleOutlined className="text-purple-600 text-2xl" />
            </div>
            <div className="text-3xl font-bold text-slate-900 mb-1">{stats.drafts}</div>
            <div className="text-slate-600 font-medium">Drafts</div>
          </div>
          
          <div className="bg-white rounded-2xl p-6 shadow-lg border border-slate-200 text-center">
            <div className="w-14 h-14 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <HeartOutlined className="text-red-600 text-2xl" />
            </div>
            <div className="text-3xl font-bold text-slate-900 mb-1">{formatNumber(stats.totalLikes)}</div>
            <div className="text-slate-600 font-medium">Total Likes</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-2xl shadow-lg border border-slate-200 mb-8 p-4">
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={[
              {
                key: 'all',
                label: (
                  <span className="flex items-center gap-2">
                    <FileTextOutlined />
                    All Articles
                  </span>
                ),
                children: (
                  <div className="p-6">
                    <ArticleList 
                      authorId={user?.id}
                      showAuthor={false}
                      limit={50}
                      showActions={true}
                      onPublishDraft={handlePublishDraft}
                    />
                  </div>
                )
              },
              {
                key: 'published',
                label: (
                  <span className="flex items-center gap-2">
                    <CheckCircleOutlined />
                    Published
                  </span>
                ),
                children: (
                  <div className="p-6">
                    <div className="text-center py-12">
                      <CheckCircleOutlined className="text-6xl text-gray-300 mb-4" />
                      <h3 className="text-xl font-semibold text-gray-600 mb-2">Published Articles</h3>
                      <p className="text-gray-500">This feature is under development!</p>
                      <p className="text-gray-400 text-sm mt-2">You can view and manage your published articles here soon.</p>
                    </div>
                  </div>
                )
              },
              {
                key: 'drafts',
                label: (
                  <span className="flex items-center gap-2">
                    <ClockCircleOutlined />
                    Drafts
                  </span>
                ),
                children: (
                  <div className="p-6">
                    <div className="text-center py-12">
                      <ClockCircleOutlined className="text-6xl text-gray-300 mb-4" />
                      <h3 className="text-xl font-semibold text-gray-600 mb-2">Draft Articles</h3>
                      <p className="text-gray-500">This feature is under development!</p>
                      <p className="text-gray-400 text-sm mt-2">You can manage your draft articles here soon.</p>
                    </div>
                  </div>
                )
              },
              {
                key: 'analytics',
                label: (
                  <span className="flex items-center gap-2">
                    <BarChartOutlined />
                    Analytics
                  </span>
                ),
                children: (
                  <div className="p-6">
                    <div className="text-center py-12">
                      <BarChartOutlined className="text-6xl text-gray-300 mb-4" />
                      <h3 className="text-xl font-semibold text-gray-600 mb-2">Analytics Dashboard</h3>
                      <p className="text-gray-500">Detailed analytics and insights coming soon!</p>
                    </div>
                  </div>
                )
              }
            ]}
          />
        </div>

        {/* Publish Draft Modal */}
        <Modal
          title="Publish Draft"
          open={publishModalVisible}
          onCancel={() => setPublishModalVisible(false)}
          footer={[
            <Button key="cancel" onClick={() => setPublishModalVisible(false)}>
              Cancel
            </Button>,
            <Button 
              key="publish" 
              type="primary" 
              loading={publishing}
              onClick={confirmPublish}
              className="bg-green-600 hover:bg-green-700"
            >
              Publish Article
            </Button>
          ]}
        >
          <div className="py-4">
            <p className="text-gray-700 mb-4">
              Are you sure you want to publish <strong>"{selectedArticle?.title}"</strong>?
            </p>
            <p className="text-gray-500 text-sm">
              Once published, the article will be visible to all users and can no longer be edited as a draft.
            </p>
          </div>
        </Modal>
      </div>
    </div>
  );
};

export default MyArticles;
