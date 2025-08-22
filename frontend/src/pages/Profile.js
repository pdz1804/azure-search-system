import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
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
  Spin,
  Modal,
  List
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

  const [followingModalVisible, setFollowingModalVisible] = useState(false);
  const [followingList, setFollowingList] = useState([]);
  const [followingLoading, setFollowingLoading] = useState(false);
  const [followersModalVisible, setFollowersModalVisible] = useState(false);
  const [followersList, setFollowersList] = useState([]);
  const [followersLoading, setFollowersLoading] = useState(false);

  const isOwnProfile = (!!currentUser && (!id || id === currentUser.id));
  const targetUserId = id || currentUser?.id;

  useEffect(() => {
    if (!targetUserId) return;

    const run = async () => {
      const fetched = await fetchUserData();
      await fetchUserStats(fetched);
      if (isAuthenticated() && !isOwnProfile) {
        checkFollowStatus();
      }
    };

    run();
  }, [targetUserId]);

  const fetchUserData = async () => {
    try {
      if (!targetUserId) return;
      const response = await userApi.getUserById(targetUserId);
      if (response.success) {
        setUser(response.data);
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to fetch user');
      }
    } catch (error) {
      message.error('Failed to load user information');
      console.error('Error fetching user:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleShowFollowing = async () => {
    // Show modal and fetch profiles of users this user follows
    if (!user) return;
    let followingArr = Array.isArray(user.following) ? user.following : [];

    // If frontend didn't receive the following array but stats suggest they follow people, re-fetch user
    if (followingArr.length === 0 && stats.following > 0) {
      const fresh = await userApi.getUserById(targetUserId).catch(() => null);
      if (fresh && fresh.success && fresh.data) {
        setUser(fresh.data);
        followingArr = Array.isArray(fresh.data.following) ? fresh.data.following : [];
      }

      // If still empty, fallback to querying all users and find the user document there
      if (followingArr.length === 0) {
        const all = await userApi.getAllUsers(1, 1000).catch(() => ({ success: false }));
        if (all && all.success !== false && Array.isArray(all.data)) {
          const found = all.data.find(u => (u.id === targetUserId) || (u._id === targetUserId));
          if (found) {
            setUser(found);
            followingArr = Array.isArray(found.following) ? found.following : [];
          }
        }
      }
    }

    if (followingArr.length === 0) {
      message.info('This user is not following anyone');
      return;
    }

    setFollowingModalVisible(true);
    setFollowingLoading(true);
    try {
      // normalize to ids
      const ids = followingArr.map(f => (typeof f === 'string' ? f : f.id || f._id)).filter(Boolean);
      const promises = ids.map(id => userApi.getUserById(id).catch(e => ({ success: false })) );
      const results = await Promise.all(promises);
      const users = results.map(r => (r && r.success && r.data) ? r.data : null).filter(Boolean);
      setFollowingList(users);
    } catch (error) {
      console.error('Failed to fetch following list', error);
      message.error('Failed to load following list');
    } finally {
      setFollowingLoading(false);
    }
  };

  const handleShowFollowers = async () => {
    if (!user) return;

    let followersArr = Array.isArray(user.followers) ? user.followers : [];

    // If missing but stat shows followers, try re-fetching user
    if (followersArr.length === 0 && stats.followers > 0) {
      const fresh = await userApi.getUserById(targetUserId).catch(() => null);
      if (fresh && fresh.success && fresh.data) {
        setUser(fresh.data);
        followersArr = Array.isArray(fresh.data.followers) ? fresh.data.followers : [];
      }
      if (followersArr.length === 0) {
        const all = await userApi.getAllUsers(1, 1000).catch(() => ({ success: false }));
        if (all && all.success !== false && Array.isArray(all.data)) {
          const found = all.data.find(u => (u.id === targetUserId) || (u._id === targetUserId));
          if (found) {
            setUser(found);
            followersArr = Array.isArray(found.followers) ? found.followers : [];
          }
        }
      }
    }

    if (followersArr.length === 0) {
      if (stats.followers > 0) {
        message.info('This user has followers but the detailed list is not available');
      } else {
        message.info('This user has no followers');
      }
      return;
    }

    setFollowersModalVisible(true);
    setFollowersLoading(true);
    try {
      const ids = followersArr.map(f => (typeof f === 'string' ? f : f.id || f._id)).filter(Boolean);
      const promises = ids.map(id => userApi.getUserById(id).catch(() => ({ success: false })));
      const results = await Promise.all(promises);
      const users = results.map(r => (r && r.success && r.data) ? r.data : null).filter(Boolean);
      setFollowersList(users);
    } catch (error) {
      console.error('Failed to fetch followers list', error);
      message.error('Failed to load followers list');
    } finally {
      setFollowersLoading(false);
    }
  };

  const fetchUserStats = async (userObj = null) => {
    try {
      if (!targetUserId) return;
      const articlesResponse = await articleApi.getArticlesByAuthor(targetUserId, 1, 1000);
      if (articlesResponse.success) {
        const articles = (articlesResponse.data?.items) || (Array.isArray(articlesResponse.data) ? articlesResponse.data : []) || [];

        const totalViews = articles.reduce((sum, article) => sum + (article.views || 0), 0);
        const totalLikes = articles.reduce((sum, article) => sum + (article.likes || 0), 0);

        const u = userObj || user || {};

        // Normalize followers/following to numeric counts
        const followersCount = (typeof u.num_followers === 'number')
          ? u.num_followers
          : Array.isArray(u.followers)
            ? u.followers.length
            : Number(u.followers) || 0;

        const followingCount = (typeof u.num_following === 'number')
          ? u.num_following
          : Array.isArray(u.following)
            ? u.following.length
            : Number(u.following) || 0;

        setStats({
          totalArticles: articles.length,
          totalViews,
          totalLikes,
          followers: followersCount,
          following: followingCount
        });

        console.log('User stats updated:', { totalViews, totalLikes, articleCount: articles.length, followersCount });
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
      // Refresh user data and stats after follow/unfollow to reflect updated followers
      const fresh = await fetchUserData();
      await fetchUserStats(fresh);
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
    <Layout style={{ minHeight: '100vh', background: 'var(--bg)' }}>
      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <Card className="bg-surface border-surface" style={{ marginBottom: 24 }}>
            <Row gutter={[24, 24]}>
              <Col xs={24} md={8}>
                <div style={{ textAlign: 'center' }} className="text-center">
                  <Avatar 
                    size={120} 
                    src={user.avatar_url}
                    style={{ marginBottom: 16 }}
                  >
                    {user.full_name?.[0]}
                  </Avatar>
                  <Title level={2} className="text-surface">{user.full_name}</Title>
                  <Text className="text-muted">{user.email}</Text>
                  <br />
                  <Text className="text-muted">
                    Joined {formatDate(user.created_at)}
                  </Text>
                  <br />
                  <Text style={{ cursor: 'pointer' }} onClick={handleShowFollowing}>
                    {stats.following} Following
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
                    <div style={{ cursor: 'pointer', textAlign: 'center' }} onClick={handleShowFollowers}>
                      <Statistic
                        title="Followers"
                        value={stats.followers}
                        prefix={<UserAddOutlined />}
                      />
                    </div>
                  </Col>
                </Row>
              </Col>
            </Row>
          </Card>

          <Modal
            title={`${user?.full_name || 'User'} - Following`}
            visible={followingModalVisible}
            onCancel={() => setFollowingModalVisible(false)}
            footer={null}
            width={600}
          >
            <List
              loading={followingLoading}
              itemLayout="horizontal"
              dataSource={followingList}
              renderItem={item => (
                <List.Item>
                  <List.Item.Meta
                    avatar={<Avatar src={item.avatar_url}>{item.full_name?.[0]}</Avatar>}
                    title={<Link to={`/profile/${item.id || item._id}`}>{item.full_name}</Link>}
                    description={item.bio || item.email}
                  />
                </List.Item>
              )}
            />
          </Modal>

          <Modal
            title={`${user?.full_name || 'User'} - Followers`}
            visible={followersModalVisible}
            onCancel={() => setFollowersModalVisible(false)}
            footer={null}
            width={600}
          >
            <List
              loading={followersLoading}
              itemLayout="horizontal"
              dataSource={followersList}
              renderItem={item => (
                <List.Item>
                  <List.Item.Meta
                    avatar={<Avatar src={item.avatar_url}>{item.full_name?.[0]}</Avatar>}
                    title={<Link to={`/profile/${item.id || item._id}`}>{item.full_name}</Link>}
                    description={item.bio || item.email}
                  />
                </List.Item>
              )}
            />
          </Modal>

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
