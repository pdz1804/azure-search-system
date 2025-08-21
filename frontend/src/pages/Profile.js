import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { 
  Layout, 
  Card, 
  Avatar, 
  Typography, 
  Space, 
  Button, 
  Statistic, 
  Row, 
  Col,
  message,
  Spin
} from 'antd';
import { 
  UserAddOutlined, 
  UserDeleteOutlined,
  EditOutlined,
  FileTextOutlined,
  EyeOutlined,
  HeartOutlined
} from '@ant-design/icons';
import { userApi } from '../api/userApi';
import { articleApi } from '../api/articleApi';
import { useAuth } from '../context/AuthContext';
import ArticleList from '../components/ArticleList';
import { formatDate, formatNumber } from '../utils/helpers';

const { Content } = Layout;
const { Title, Text } = Typography;

const Profile = () => {
  const { id } = useParams();
  const { user: currentUser, isAuthenticated } = useAuth();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isFollowing, setIsFollowing] = useState(false);
  const [stats, setStats] = useState({
    totalArticles: 0,
    totalViews: 0,
    totalLikes: 0,
    followers: 0,
    following: 0
  });

  const isOwnProfile = id === currentUser?.id || (!id && currentUser);
  const targetUserId = id || currentUser?.id;

  useEffect(() => {
    if (targetUserId) {
      fetchUserData();
      fetchUserStats();
      if (isAuthenticated() && !isOwnProfile) {
        checkFollowStatus();
      }
    }
  }, [targetUserId]);

  const fetchUserData = async () => {
    try {
      let userData;
      if (isOwnProfile && !id) {
        userData = currentUser;
      } else {
        const response = await userApi.getUserById(targetUserId);
        if (response.success) {
          userData = response.data;
        } else {
          throw new Error(response.error || 'Failed to fetch user');
        }
      }
      setUser(userData);
    } catch (error) {
      message.error('Failed to load user information');
      console.error('Error fetching user:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUserStats = async () => {
    try {
      const articlesResponse = await articleApi.getArticlesByAuthor(targetUserId, 1, 1000);
      if (articlesResponse.success) {
        const articles = articlesResponse.data?.items || articlesResponse.data || [];
        
        const totalViews = articles.reduce((sum, article) => sum + (article.views || 0), 0);
        const totalLikes = articles.reduce((sum, article) => sum + (article.likes || 0), 0);
        
        setStats({
          totalArticles: articles.length,
          totalViews,
          totalLikes,
          followers: user?.followers?.length || 0,
          following: user?.following?.length || 0
        });
        
        console.log('User stats updated:', { totalViews, totalLikes, articleCount: articles.length });
      }
    } catch (error) {
      console.error('Error fetching user stats:', error);
    }
  };

  const checkFollowStatus = async () => {
    try {
      const response = await userApi.checkFollowStatus(targetUserId);
      setIsFollowing(response.is_following);
    } catch (error) {
      // Silent fail
    }
  };

  const handleFollow = async () => {
    if (!isAuthenticated()) {
      message.warning('Please log in to follow');
      return;
    }
    
    try {
      if (isFollowing) {
        await userApi.unfollowUser(targetUserId);
        message.success('Unfollowed');
        setIsFollowing(false);
      } else {
        await userApi.followUser(targetUserId);
        message.success('Followed');
        setIsFollowing(true);
      }
      fetchUserStats();
    } catch (error) {
      message.error('Failed to perform action');
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!user) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Title level={3}>User not found</Title>
      </div>
    );
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <Card style={{ marginBottom: 24 }}>
            <Row gutter={[24, 24]}>
              <Col xs={24} md={8}>
                <div style={{ textAlign: 'center' }}>
                  <Avatar 
                    size={120} 
                    src={user.avatar_url}
                    style={{ marginBottom: 16 }}
                  >
                    {user.full_name?.[0]}
                  </Avatar>
                  <Title level={2}>{user.full_name}</Title>
                  <Text type="secondary">{user.email}</Text>
                  <br />
                  <Text type="secondary">
                    Joined {formatDate(user.created_at)}
                  </Text>
                  
                  {!isOwnProfile && isAuthenticated() && (
                    <div style={{ marginTop: 16 }}>
                      <Button
                        type={isFollowing ? "default" : "primary"}
                        icon={isFollowing ? <UserDeleteOutlined /> : <UserAddOutlined />}
                        onClick={handleFollow}
                      >
                        {isFollowing ? 'Unfollow' : 'Follow'}
                      </Button>
                    </div>
                  )}
                  
                  {isOwnProfile && (
                    <div style={{ marginTop: 16 }}>
                      <Button
                        type="primary"
                        icon={<EditOutlined />}
                        onClick={() => message.info('Edit profile functionality will be developed')}
                      >
                        Edit Profile
                      </Button>
                    </div>
                  )}
                </div>
              </Col>
              
              <Col xs={24} md={16}>
                <Row gutter={[16, 16]}>
                  <Col xs={12} sm={6}>
                    <Statistic
                      title="Articles"
                      value={stats.totalArticles}
                      prefix={<FileTextOutlined />}
                    />
                  </Col>
                  <Col xs={12} sm={6}>
                    <Statistic
                      title="Views"
                      value={formatNumber(stats.totalViews)}
                      prefix={<EyeOutlined />}
                    />
                  </Col>
                  <Col xs={12} sm={6}>
                    <Statistic
                      title="Likes"
                      value={formatNumber(stats.totalLikes)}
                      prefix={<HeartOutlined />}
                    />
                  </Col>
                  <Col xs={12} sm={6}>
                    <Statistic
                      title="Followers"
                      value={stats.followers}
                      prefix={<UserAddOutlined />}
                    />
                  </Col>
                </Row>
              </Col>
            </Row>
          </Card>

          <ArticleList 
            authorId={targetUserId}
            title={isOwnProfile ? "Your Articles" : `Articles by ${user.full_name}`}
          />
        </div>
      </Content>
    </Layout>
  );
};

export default Profile;
