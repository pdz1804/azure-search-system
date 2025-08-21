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
  const [searchType, setSearchType] = useState('general'); // 'general', 'authors', 'articles'

  useEffect(() => {
    if (query) {
      analyzeQueryAndSearch();
    }
  }, [query]);

  // Debug: Monitor articles state changes
  useEffect(() => {
    console.log('🔄 Articles state changed:', articles.length, 'articles');
    console.log('🔄 Articles data:', articles);
  }, [articles]);

  // Debug: Monitor users state changes
  useEffect(() => {
    console.log('🔄 Users state changed:', users.length, 'users');
  }, [users]);

  // Force re-render when search completes
  const [searchCompleted, setSearchCompleted] = useState(false);

  const analyzeQueryAndSearch = async () => {
    setLoading(true);
    setArticles([]); // Clear previous results
    setUsers([]);    // Clear previous results
    
    try {
      console.log('🔍 Starting search analysis for query:', query);
      
      // Analyze the query to determine search type
      const queryLower = query.toLowerCase();
      const isAuthorSearch = queryLower.includes('author') || 
                           queryLower.includes('người dùng') || 
                           queryLower.includes('user') ||
                           queryLower.includes('tác giả');
      
      if (isAuthorSearch) {
        console.log('👥 Detected author search, searching users only');
        setSearchType('authors');
        setActiveTab('users');
        const usersResult = await searchUsersAI();
        console.log('👥 Users search completed with:', usersResult.length, 'results');
      } else {
        console.log('📚 Detected general search, searching articles only');
        setSearchType('general');
        // Only search articles for general queries, not users
        const articlesResult = await searchArticles();
        console.log('📚 Articles search completed with:', articlesResult.length, 'results');
      }
      
      console.log('✅ Search analysis completed');
      setSearchCompleted(true); // Mark search as completed
    } catch (error) {
      console.error('❌ Search analysis error:', error);
      message.error('An error occurred while searching');
    } finally {
      setLoading(false);
    }
  };

  const searchArticles = async () => {
    try {
      console.log('🔍 Starting articles search for query:', query);
      
      // Wait for the API call to complete
      const response = await articleApi.searchArticles(query, 10, 1, 50);
      console.log('🔍 Articles search response:', response);
      console.log('🔍 Response type:', typeof response);
      console.log('🔍 Response keys:', Object.keys(response || {}));
      
      // Backend returns results in "results" property, not "data"
      const articlesData = response.results || response.data || [];
      console.log('📚 Articles data to display:', articlesData);
      console.log('📚 Articles count:', articlesData.length);
      console.log('📚 First article sample:', articlesData[0]);
      
      // Set articles state
      setArticles(articlesData);
      
      // Wait for state to be updated
      await new Promise(resolve => setTimeout(resolve, 200));
      
      console.log('✅ Articles state updated, current count:', articlesData.length);
      
      // Return the data to ensure it's processed
      return articlesData;
    } catch (error) {
      console.error('Search articles error:', error);
      setArticles([]);
      return [];
    }
  };

  const searchUsersAI = async () => {
    try {
      console.log('🔍 Starting users AI search for query:', query);
      
      // Try AI-powered search first
      const response = await userApi.searchUsersAI({
        q: query,
        page: 1,
        limit: 50
      });
      
      console.log('🔍 Users search response:', response);
      // Backend returns results in "results" property, not "data"
      let usersData = [];
      
      if (response.success && response.results && response.results.length > 0) {
        console.log('👥 Users data (with success):', response.results);
        usersData = response.results;
      } else if (response.results && response.results.length > 0) {
        // Direct results without success flag
        console.log('👥 Users data (direct):', response.results);
        usersData = response.results;
      } else {
        console.log('⚠️ No users found in response, trying fallback...');
        // Fallback to simple search
        const simpleResponse = await userApi.searchUsers({
          q: query
        });
        usersData = simpleResponse.data || simpleResponse || [];
      }
      
      // Set users state
      setUsers(usersData);
      
      // Wait for state to be updated
      await new Promise(resolve => setTimeout(resolve, 200));
      
      console.log('✅ Users state updated, current count:', usersData.length);
      
      return usersData;
    } catch (error) {
      console.error('Search users error:', error);
      // Fallback to simple search
      try {
        const simpleResponse = await userApi.searchUsers({
          q: query
        });
        const fallbackData = simpleResponse.data || simpleResponse || [];
        setUsers(fallbackData);
        return fallbackData;
      } catch (fallbackError) {
        console.error('Fallback search also failed:', fallbackError);
        setUsers([]);
        return [];
      }
    }
  };

  const searchUsers = async () => {
    try {
      const response = await userApi.searchUsers({
        q: query
      });
      setUsers(response.data || response || []);
    } catch (error) {
      console.error('Search users error:', error);
      setUsers([]);
    }
  };

  const renderUserCard = (user) => (
    <Card key={user.id || user._id} style={{ marginBottom: 16 }}>
      <Row align="middle" gutter={16}>
        <Col>
          <Avatar size={64} src={user.avatar_url || user.avatar}>
            {user.full_name?.[0] || user.name?.[0] || 'U'}
          </Avatar>
        </Col>
        <Col flex="auto">
          <Space direction="vertical" size="small">
            <Title level={4} style={{ margin: 0 }}>
              <Link to={`/profile/${user.id || user._id}`}>
                {user.full_name || user.name || 'Unknown User'}
              </Link>
            </Title>
            <Text type="secondary">{user.email || 'No email provided'}</Text>
            {user.bio && (
              <Text>{user.bio}</Text>
            )}
            {user.score && (
              <Text type="secondary">Score: {user.score.toFixed(2)}</Text>
            )}
            {user.search_source && (
              <Text type="secondary" style={{ fontSize: '12px' }}>
                Source: {user.search_source === 'ai_search' ? 'AI Search' : 'AI Search + Database'}
              </Text>
            )}
          </Space>
        </Col>
        <Col>
          <Button type="primary">
            <Link to={`/profile/${user.id || user._id}`}>
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
            {searchType === 'authors' && (
              <Text type="secondary" style={{ fontSize: 16 }}>
                Tìm kiếm tác giả với AI
              </Text>
            )}
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
                        description={
                          searchType === 'authors' 
                            ? "Không tìm thấy bài viết nào cho tìm kiếm tác giả"
                            : "Không tìm thấy bài viết nào"
                        }
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
                        description={
                          searchType === 'authors' 
                            ? "Không tìm thấy tác giả nào với tên 'Chuonggg'"
                            : "Không tìm thấy người dùng nào"
                        }
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
