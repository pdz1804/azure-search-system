import React, { useState, useEffect } from 'react';
import { 
  Layout, 
  Typography, 
  Empty,
  message,
  Card,
  Spin
} from 'antd';
import { HeartOutlined } from '@ant-design/icons';
import ArticleList from '../components/ArticleList';
import { userApi } from '../api/userApi';
import { useAuth } from '../context/AuthContext';

const { Content } = Layout;
const { Title, Text } = Typography;

/**
 * Bookmarks Page - Displays user's bookmarked articles
 * Uses modern Tailwind styling with proper API integration
 */
const Bookmarks = () => {
  const { user, isAuthenticated } = useAuth();
  const [bookmarkedArticles, setBookmarkedArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isAuthenticated()) {
      fetchBookmarkedArticles();
    } else {
      setLoading(false);
    }
  }, [user]);

  const fetchBookmarkedArticles = async () => {
    try {
      setLoading(true);
      console.log('Fetching bookmarked articles...');
      
      // Use the proper API endpoint to get bookmarked articles
      const response = await userApi.getBookmarkedArticles();
      console.log('Bookmarks API response:', response);
      
      if (response.success) {
        const articles = response.data || [];
        console.log('Setting bookmarked articles:', articles);
        setBookmarkedArticles(articles);
      } else {
        console.error('Failed to fetch bookmarks:', response.error);
        setBookmarkedArticles([]);
      }
    } catch (error) {
      console.error('Error fetching bookmarked articles:', error);
      message.error('Failed to load bookmarked articles');
      setBookmarkedArticles([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveBookmark = (articleId) => {
    setBookmarkedArticles(prev => prev.filter(article => article.id !== articleId));
  };

  if (!loading && bookmarkedArticles.length === 0) {
    return (
      <Layout style={{ minHeight: '100vh', background: '#f8f9fa' }}>
        <Content style={{ padding: '24px' }}>
          <div style={{ maxWidth: 800, margin: '0 auto' }}>
            <Title level={2} style={{ 
              color: '#1a1a1a',
              textAlign: 'center',
              marginBottom: 32
            }}>
              <HeartOutlined style={{ marginRight: 8, color: '#ff4d4f' }} />
              Saved Articles
            </Title>
            
            <Card style={{ 
              borderRadius: 16,
              boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
              border: 'none',
              textAlign: 'center'
            }}>
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description={
                  <div>
                    <Text style={{ fontSize: 16, color: '#1a1a1a' }}>
                      You haven't saved any articles yet
                    </Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: 14 }}>
                      Click the heart icon on articles to save them here
                    </Text>
                  </div>
                }
              />
            </Card>
          </div>
        </Content>
      </Layout>
    );
  }

  return (
    <Layout style={{ minHeight: '100vh', background: '#f8f9fa' }}>
      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <Title level={2} style={{ 
            color: '#1a1a1a',
            marginBottom: 32
          }}>
            <HeartOutlined style={{ marginRight: 8, color: '#ff4d4f' }} />
            Saved Articles ({bookmarkedArticles.length})
          </Title>
          
          <ArticleList 
            articles={bookmarkedArticles}
            loading={loading}
            showLoadMore={false}
            onBookmarkChange={handleRemoveBookmark}
          />
        </div>
      </Content>
    </Layout>
  );
};

export default Bookmarks;
