import React, { useState, useEffect } from 'react';
import { 
  Layout, 
  Typography, 
  Row, 
  Col, 
  Card, 
  Statistic,
  Spin,
  message,
  Progress
} from 'antd';
import { 
  FileTextOutlined,
  EyeOutlined,
  HeartOutlined,
  UserOutlined,
  TrophyOutlined,
  RiseOutlined
} from '@ant-design/icons';
import { articleApi } from '../api/articleApi';
import { useAuth } from '../context/AuthContext';
import { formatNumber } from '../utils/helpers';

const { Content } = Layout;
const { Title, Text } = Typography;

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      // Fetch global stats for admin or personal stats for writers
      if (user?.role === 'admin') {
        try {
          const globalStats = await articleApi.getSummary();
          setStats(globalStats);
        } catch (error) {
          console.error('Failed to fetch global stats:', error);
          // Fallback to personal stats if global fails
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
      } else if (user?.role === 'writer') {
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
      <Layout style={{ minHeight: '100vh' }}>
        <Content style={{ padding: '24px' }}>
          <div style={{ textAlign: 'center', paddingTop: '50px' }}>
            <Spin size="large" />
          </div>
        </Content>
      </Layout>
    );
  }

  const isAdmin = user?.role === 'admin';
  const publishRate = stats?.total_articles > 0 
    ? Math.round((stats.published_articles / stats.total_articles) * 100) 
    : 0;

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 48 }}>
            <Title level={1} style={{ 
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              marginBottom: 16
            }}>
              Dashboard
            </Title>
            <Text style={{ fontSize: 18, color: '#666' }}>
              {user?.role === 'admin' ? 'Global system overview and analytics' : 'Your personal writing statistics'}
            </Text>
          </div>

          <Row gutter={[24, 24]}>
            <Col xs={24} sm={12} lg={6}>
              <Card style={{ 
                borderRadius: 16,
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                border: 'none',
                textAlign: 'center'
              }}>
                <Statistic
                  title="Total Articles"
                  value={stats.total_articles || 0}
                  prefix={<FileTextOutlined style={{ color: '#1890ff' }} />}
                  valueStyle={{ color: '#1a1a1a', fontSize: 24 }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card style={{ 
                borderRadius: 16,
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                border: 'none',
                textAlign: 'center'
              }}>
                <Statistic
                  title="Published"
                  value={stats.published_articles || 0}
                  prefix={<FileTextOutlined style={{ color: '#52c41a' }} />}
                  valueStyle={{ color: '#1a1a1a', fontSize: 24 }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card style={{ 
                borderRadius: 16,
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                border: 'none',
                textAlign: 'center'
              }}>
                <Statistic
                  title="Total Views"
                  value={formatNumber(stats.total_views || 0)}
                  prefix={<EyeOutlined style={{ color: '#722ed1' }} />}
                  valueStyle={{ color: '#1a1a1a', fontSize: 24 }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card style={{ 
                borderRadius: 16,
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                border: 'none',
                textAlign: 'center'
              }}>
                <Statistic
                  title="Total Likes"
                  value={formatNumber(stats.total_likes || 0)}
                  prefix={<HeartOutlined style={{ color: '#ff4d4f' }} />}
                  valueStyle={{ color: '#1a1a1a', fontSize: 24 }}
                />
              </Card>
            </Col>
          </Row>

          <Row gutter={[16, 16]}>
            {isAdmin && (
              <Col xs={24} md={12}>
                <Card title="Overview Statistics">
                  <Row gutter={[16, 16]}>
                    <Col span={12}>
                      <Statistic
                        title="Total Authors"
                        value={stats?.authors || 0}
                        prefix={<UserOutlined />}
                      />
                    </Col>
                    <Col span={12}>
                      <Statistic
                        title="Drafts"
                        value={stats?.drafts || stats?.draft_articles || 0}
                        prefix={<FileTextOutlined />}
                      />
                    </Col>
                  </Row>
                </Card>
              </Col>
            )}
            
            <Col xs={24} md={isAdmin ? 12 : 24}>
              <Card title="Publication Rate">
                <Progress
                  type="circle"
                  percent={publishRate}
                  format={percent => `${percent}%`}
                  size={120}
                  strokeColor={{
                    '0%': '#108ee9',
                    '100%': '#87d068',
                  }}
                />
                <div style={{ textAlign: 'center', marginTop: 16 }}>
                  <div>
                    {stats?.published_articles || stats?.published || 0} / {stats?.total_articles || stats?.total || 0} articles
                  </div>
                </div>
              </Card>
            </Col>

            {!isAdmin && (
              <Col xs={24} md={12}>
                <Card title="Performance">
                  <Statistic
                    title="Average Views/Article"
                    value={stats?.avg_views || 0}
                    prefix={<EyeOutlined />}
                    suffix="views"
                  />
                  <div style={{ marginTop: 16 }}>
                    <Statistic
                      title="Engagement Rate"
                      value={stats?.total_views > 0 ? Math.round((stats.total_likes / stats.total_views) * 100 * 100) / 100 : 0}
                      suffix="%"
                      precision={2}
                      prefix={<HeartOutlined />}
                    />
                  </div>
                </Card>
              </Col>
            )}
          </Row>
        </div>
      </Content>
    </Layout>
  );
};

export default Dashboard;
