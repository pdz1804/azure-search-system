/* eslint-disable */
/* @ts-nocheck */
/* JAF-ignore */
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
      // Request server-side page 1 with page_size=12 (backend expects page_index 0-based)
      const response = await articleApi.searchArticles(query, 12, 1, 60);
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
      // Request authors with page_size=12
      const response = await userApi.searchUsersAI({
        q: query,
        page: 1,
        limit: 12
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
        usersData = [];
      }
      
      // Set users state
      setUsers(usersData);
      
      // Wait for state to be updated
      await new Promise(resolve => setTimeout(resolve, 200));
      
      console.log('✅ Users state updated, current count:', usersData.length);
      
      return usersData;
    } catch (error) {
      console.error('Search users error:', error);
      setUsers([]);
      return [];
    }
  };

  // Removed simple user search to adhere to allowed endpoints only

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
              View Profile
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
            <Title level={3}>Search Articles and Users</Title>
            <Text type="secondary">
              Use the search bar above to search for articles and users
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
            {/* <Title level={2}>
              Search results for "{query}"
            </Title> */}
            {searchType === 'authors' && (
              <Text type="secondary" style={{ fontSize: 16 }}>
                AI-powered author search
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
                    Articles
                  </span>
                ),
                children: (
                  <div>
                    {loading ? (
                      <div style={{ textAlign: 'center', padding: '50px' }}>
                        <Spin size="large" />
                      </div>
                    ) : searchType === 'authors' ? (
                      // Don't show articles for author-specific searches
                      <Empty 
                        description="Switch to 'Users' tab to see author search results"
                        image={Empty.PRESENTED_IMAGE_SIMPLE}
                      />
                    ) : (
                      // Let ArticleList handle fetching, pagination and empty state
                      <ArticleList 
                        searchQuery={query}
                        showLoadMore={true}
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
                    Users ({users.length})
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
                            ? "No authors found matching the search"
                            : "No users found"
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
