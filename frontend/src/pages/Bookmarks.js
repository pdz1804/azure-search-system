import React, { useState, useEffect } from 'react';
import { 
  Layout, 
  Typography, 
  Empty,
  message,
  Card
} from 'antd';
import { HeartOutlined } from '@ant-design/icons';
import ArticleList from '../components/ArticleList';
import { articleApi } from '../api/articleApi';
import { useAuth } from '../context/AuthContext';

const { Content } = Layout;
const { Title, Text } = Typography;

const Bookmarks = () => {
  const { user } = useAuth();
  const [bookmarkedArticles, setBookmarkedArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user?.bookmarked_articles) {
      fetchBookmarkedArticles();
    } else {
      setLoading(false);
    }
  }, [user]);

  const fetchBookmarkedArticles = async () => {
    try {
      if (!user.bookmarked_articles || user.bookmarked_articles.length === 0) {
        setBookmarkedArticles([]);
        setLoading(false);
        return;
      }

      const articles = await Promise.all(
        user.bookmarked_articles.map(async (articleId) => {
          try {
            return await articleApi.getArticle(articleId);
          } catch (error) {
            console.error(`Error fetching article ${articleId}:`, error);
            return null;
          }
        })
      );

      // Filter out null values (failed requests)
      setBookmarkedArticles(articles.filter(article => article !== null));
    } catch (error) {
      message.error('Không thể tải danh sách bài viết đã lưu');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveBookmark = (articleId) => {
    setBookmarkedArticles(prev => prev.filter(article => article.id !== articleId));
  };

  if (!loading && bookmarkedArticles.length === 0) {
    return (
      <Layout style={{ minHeight: '100vh' }}>
        <Content style={{ padding: '24px' }}>
          <div style={{ maxWidth: 800, margin: '0 auto' }}>
            <Title level={2}>
              <HeartOutlined style={{ marginRight: 8 }} />
              Bài viết đã lưu
            </Title>
            
            <Card>
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description={
                  <div>
                    <Text>Bạn chưa lưu bài viết nào</Text>
                    <br />
                    <Text type="secondary">
                      Nhấn vào biểu tượng trái tim ở các bài viết để lưu chúng vào đây
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
    <Layout style={{ minHeight: '100vh' }}>
      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <Title level={2}>
            <HeartOutlined style={{ marginRight: 8 }} />
            Bài viết đã lưu ({bookmarkedArticles.length})
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
