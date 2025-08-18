import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { 
  Layout, 
  Typography, 
  Space,
  Tabs,
  Empty,
  Spin,
  message,
  Row,
  Col,
  Card,
  Avatar,
  Button
} from 'antd';
import { 
  FileTextOutlined, 
  UserOutlined,
  SearchOutlined
} from '@ant-design/icons';
import { articleApi } from '../api/articleApi';
import { userApi } from '../api/userApi';
import ArticleList from '../components/ArticleList';
import { Link } from 'react-router-dom';

const { Content } = Layout;
const { Title, Text } = Typography;
const { TabPane } = Tabs;

const Search = () => {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  const [loading, setLoading] = useState(false);
  const [articles, setArticles] = useState([]);
  const [users, setUsers] = useState([]);
  const [activeTab, setActiveTab] = useState('articles');

  useEffect(() => {
    if (query) {
      searchAll();
    }
  }, [query]);

  const searchAll = async () => {
    setLoading(true);
    try {
      await Promise.all([
        searchArticles(),
        searchUsers()
      ]);
    } catch (error) {
      message.error('Có lỗi xảy ra khi tìm kiếm');
    } finally {
      setLoading(false);
    }
  };

  const searchArticles = async () => {
    try {
      const response = await articleApi.searchArticles({
        q: query,
        page: 1,
        limit: 50
      });
      setArticles(response.items || []);
    } catch (error) {
      console.error('Search articles error:', error);
    }
  };

  const searchUsers = async () => {
    try {
      const response = await userApi.searchUsers({
        q: query,
        page: 1,
        limit: 50
      });
      setUsers(response.items || []);
    } catch (error) {
      console.error('Search users error:', error);
    }
  };

  const renderUserCard = (user) => (
    <Card key={user.id} style={{ marginBottom: 16 }}>
      <Row align="middle" gutter={16}>
        <Col>
          <Avatar size={64} src={user.avatar_url}>
            {user.full_name?.[0]}
          </Avatar>
        </Col>
        <Col flex="auto">
          <Space direction="vertical" size="small">
            <Title level={4} style={{ margin: 0 }}>
              <Link to={`/profile/${user.id}`}>
                {user.full_name}
              </Link>
            </Title>
            <Text type="secondary">{user.email}</Text>
            {user.bio && (
              <Text>{user.bio}</Text>
            )}
          </Space>
        </Col>
        <Col>
          <Button type="primary">
            <Link to={`/profile/${user.id}`}>
              Xem hồ sơ
            </Link>
          </Button>
        </Col>
      </Row>
    </Card>
  );

  if (!query) {
    return (
      <Layout style={{ minHeight: '100vh' }}>
        <Content style={{ padding: '24px' }}>
          <div style={{ maxWidth: 800, margin: '0 auto', textAlign: 'center', paddingTop: 50 }}>
            <SearchOutlined style={{ fontSize: 64, color: '#ccc', marginBottom: 16 }} />
            <Title level={3}>Tìm kiếm bài viết và người dùng</Title>
            <Text type="secondary">
              Sử dụng thanh tìm kiếm ở trên để tìm kiếm bài viết và người dùng
            </Text>
          </div>
        </Content>
      </Layout>
    );
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
          <div style={{ marginBottom: 24 }}>
            <Title level={2}>
              Kết quả tìm kiếm cho "{query}"
            </Title>
          </div>

          <Tabs 
            activeKey={activeTab} 
            onChange={setActiveTab}
            items={[
              {
                key: 'articles',
                label: (
                  <span>
                    <FileTextOutlined />
                    Bài viết ({articles.length})
                  </span>
                ),
                children: (
                  <div>
                    {loading ? (
                      <div style={{ textAlign: 'center', padding: '50px' }}>
                        <Spin size="large" />
                      </div>
                    ) : articles.length > 0 ? (
                      <ArticleList 
                        articles={articles}
                        showLoadMore={false}
                      />
                    ) : (
                      <Empty 
                        description="Không tìm thấy bài viết nào"
                        image={Empty.PRESENTED_IMAGE_SIMPLE}
                      />
                    )}
                  </div>
                )
              },
              {
                key: 'users',
                label: (
                  <span>
                    <UserOutlined />
                    Người dùng ({users.length})
                  </span>
                ),
                children: (
                  <div>
                    {loading ? (
                      <div style={{ textAlign: 'center', padding: '50px' }}>
                        <Spin size="large" />
                      </div>
                    ) : users.length > 0 ? (
                      <div>
                        {users.map(renderUserCard)}
                      </div>
                    ) : (
                      <Empty 
                        description="Không tìm thấy người dùng nào"
                        image={Empty.PRESENTED_IMAGE_SIMPLE}
                      />
                    )}
                  </div>
                )
              }
            ]}
          />
        </div>
      </Content>
    </Layout>
  );
};

export default Search;
