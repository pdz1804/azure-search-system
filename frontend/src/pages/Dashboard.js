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
const { Title } = Typography;

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
        const globalStats = await articleApi.getSummary();
        setStats(globalStats);
      } else if (user?.role === 'writer') {
        // Fetch personal stats
        const response = await articleApi.getArticlesByAuthor(user.id, 1, 1000);
        const articles = response.items || [];
        
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
    } catch (error) {
      message.error('Không thể tải thống kê');
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
          <Title level={2}>
            <TrophyOutlined style={{ marginRight: 8 }} />
            {isAdmin ? 'Dashboard Quản trị' : 'Dashboard Cá nhân'}
          </Title>

          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title={isAdmin ? "Tổng bài viết" : "Bài viết của tôi"}
                  value={stats?.total_articles || stats?.total || 0}
                  prefix={<FileTextOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="Đã xuất bản"
                  value={stats?.published_articles || stats?.published || 0}
                  prefix={<RiseOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="Tổng lượt xem"
                  value={formatNumber(stats?.total_views || 0)}
                  prefix={<EyeOutlined />}
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
            
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="Tổng lượt thích"
                  value={formatNumber(stats?.total_likes || 0)}
                  prefix={<HeartOutlined />}
                  valueStyle={{ color: '#f5222d' }}
                />
              </Card>
            </Col>
          </Row>

          <Row gutter={[16, 16]}>
            {isAdmin && (
              <Col xs={24} md={12}>
                <Card title="Thống kê tổng quan">
                  <Row gutter={[16, 16]}>
                    <Col span={12}>
                      <Statistic
                        title="Tổng tác giả"
                        value={stats?.authors || 0}
                        prefix={<UserOutlined />}
                      />
                    </Col>
                    <Col span={12}>
                      <Statistic
                        title="Bản nháp"
                        value={stats?.drafts || stats?.draft_articles || 0}
                        prefix={<FileTextOutlined />}
                      />
                    </Col>
                  </Row>
                </Card>
              </Col>
            )}
            
            <Col xs={24} md={isAdmin ? 12 : 24}>
              <Card title="Tỷ lệ xuất bản">
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
                    {stats?.published_articles || stats?.published || 0} / {stats?.total_articles || stats?.total || 0} bài viết
                  </div>
                </div>
              </Card>
            </Col>

            {!isAdmin && (
              <Col xs={24} md={12}>
                <Card title="Hiệu suất">
                  <Statistic
                    title="Trung bình lượt xem/bài"
                    value={stats?.avg_views || 0}
                    prefix={<EyeOutlined />}
                    suffix="views"
                  />
                  <div style={{ marginTop: 16 }}>
                    <Statistic
                      title="Tỷ lệ tương tác"
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
