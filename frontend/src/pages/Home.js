import React from 'react';
import { Layout, Typography, Button, Space } from 'antd';
import { EditOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ArticleList from '../components/ArticleList';

const { Content } = Layout;
const { Title, Paragraph } = Typography;

const Home = () => {
  const navigate = useNavigate();
  const { isAuthenticated, hasRole } = useAuth();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 48 }}>
            <Title level={1}>Chào mừng đến với Article Management</Title>
            <Paragraph style={{ fontSize: 16, color: '#666' }}>
              Nền tảng chia sẻ bài viết và kiến thức chuyên nghiệp
            </Paragraph>
            
            {isAuthenticated() && (hasRole('writer') || hasRole('admin')) && (
              <Space style={{ marginTop: 24 }}>
                <Button 
                  type="primary" 
                  size="large" 
                  icon={<EditOutlined />}
                  onClick={() => navigate('/articles/new')}
                >
                  Viết bài mới
                </Button>
              </Space>
            )}
          </div>

          <ArticleList />
        </div>
      </Content>
    </Layout>
  );
};

export default Home;
