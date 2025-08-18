import React, { useState, useEffect } from 'react';
import { 
  Layout, 
  Typography, 
  Button, 
  Space,
  Tabs,
  message,
  Row,
  Col,
  Statistic,
  Card
} from 'antd';
import { 
  PlusOutlined, 
  FileTextOutlined,
  EditOutlined,
  EyeOutlined,
  HeartOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import ArticleList from '../components/ArticleList';
import { articleApi } from '../api/articleApi';
import { useAuth } from '../context/AuthContext';
import { formatNumber } from '../utils/helpers';

const { Content } = Layout;
const { Title } = Typography;

const MyArticles = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [stats, setStats] = useState({
    total: 0,
    published: 0,
    drafts: 0,
    totalViews: 0,
    totalLikes: 0
  });

  useEffect(() => {
    if (user?.id) {
      fetchStats();
    }
  }, [user]);

  const fetchStats = async () => {
    try {
      const response = await articleApi.getArticlesByAuthor(user.id, 1, 1000);
      const articles = response.items || [];
      
      const published = articles.filter(a => a.status === 'published').length;
      const drafts = articles.filter(a => a.status === 'draft').length;
      const totalViews = articles.reduce((sum, a) => sum + (a.views || 0), 0);
      const totalLikes = articles.reduce((sum, a) => sum + (a.likes || 0), 0);
      
      setStats({
        total: articles.length,
        published,
        drafts,
        totalViews,
        totalLikes
      });
    } catch (error) {
      message.error('Không thể tải thống kê bài viết');
    }
  };

  const handleCreateArticle = () => {
    navigate('/write');
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            marginBottom: 24 
          }}>
            <Title level={2}>
              <FileTextOutlined style={{ marginRight: 8 }} />
              Bài viết của tôi
            </Title>
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              size="large"
              onClick={handleCreateArticle}
            >
              Viết bài mới
            </Button>
          </div>

          {/* Statistics */}
          <Card style={{ marginBottom: 24 }}>
            <Row gutter={[16, 16]}>
              <Col xs={12} sm={6}>
                <Statistic
                  title="Tổng bài viết"
                  value={stats.total}
                  prefix={<FileTextOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
              <Col xs={12} sm={6}>
                <Statistic
                  title="Đã xuất bản"
                  value={stats.published}
                  prefix={<EditOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Col>
              <Col xs={12} sm={6}>
                <Statistic
                  title="Tổng lượt xem"
                  value={formatNumber(stats.totalViews)}
                  prefix={<EyeOutlined />}
                  valueStyle={{ color: '#722ed1' }}
                />
              </Col>
              <Col xs={12} sm={6}>
                <Statistic
                  title="Tổng lượt thích"
                  value={formatNumber(stats.totalLikes)}
                  prefix={<HeartOutlined />}
                  valueStyle={{ color: '#f5222d' }}
                />
              </Col>
            </Row>
          </Card>

          {/* Article Lists */}
          <Tabs
            defaultActiveKey="all"
            items={[
              {
                key: 'all',
                label: `Tất cả (${stats.total})`,
                children: (
                  <ArticleList 
                    authorId={user?.id}
                    showAuthor={false}
                    onRefresh={fetchStats}
                  />
                )
              },
              {
                key: 'published',
                label: `Đã xuất bản (${stats.published})`,
                children: (
                  <ArticleList 
                    authorId={user?.id}
                    status="published"
                    showAuthor={false}
                    onRefresh={fetchStats}
                  />
                )
              },
              {
                key: 'drafts',
                label: `Bản nháp (${stats.drafts})`,
                children: (
                  <ArticleList 
                    authorId={user?.id}
                    status="draft"
                    showAuthor={false}
                    onRefresh={fetchStats}
                  />
                )
              }
            ]}
          />
        </div>
      </Content>
    </Layout>
  );
};

export default MyArticles;
