import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { message, Modal, List, Spin } from 'antd';
import {
  UserOutlined,
  EditOutlined,
  CalendarOutlined,
  EyeOutlined,
  HeartOutlined,
  FileTextOutlined,
  TeamOutlined,
  MailOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { userApi } from '../api/userApi';
import { articleApi } from '../api/articleApi';
import { useAuth } from '../context/AuthContext';
import ArticleList from '../components/ArticleList';
import DashboardStats from '../components/DashboardStats';
import { useAuthorStats } from '../hooks/useAuthorStats';
import { formatNumber } from '../utils/helpers';

const Profile = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user: currentUser, isAuthenticated } = useAuth();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isFollowing, setIsFollowing] = useState(false);
  const [followLoading, setFollowLoading] = useState(false);
  const [stats, setStats] = useState({
    totalArticles: 0,
    totalViews: 0,
    totalLikes: 0,
    followers: 0,
    following: 0
  });

  // New state variables for error handling
  const [errorType, setErrorType] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  const [followingModalVisible, setFollowingModalVisible] = useState(false);
  const [followingList, setFollowingList] = useState([]);
  const [followingLoading, setFollowingLoading] = useState(false);
  const [followersModalVisible, setFollowersModalVisible] = useState(false);
  const [followersList, setFollowersList] = useState([]);
  const [followersLoading, setFollowersLoading] = useState(false);
  const [imageViewerOpen, setImageViewerOpen] = useState(false);

  const isOwnProfile = (!!currentUser && (!id || id === currentUser.id));
  const targetUserId = id || currentUser?.id;

  // Use the shared hook for author stats to prevent duplicate API calls
  const { stats: authorStats } = useAuthorStats(targetUserId, { 
    enabled: !!targetUserId,
    limit: 50 // Lighter load for profile view
  });

  useEffect(() => {
    if (!targetUserId) return;

    const run = async () => {
      setLoading(true);
      try {
        // Fetch user data first (needed by fetchUserStats)
        const fetched = await fetchUserData();
        
        // Run follow status check if needed
        const promises = [];
        
        if (isAuthenticated() && !isOwnProfile) {
          promises.push(checkFollowStatus());
        }
        
        await Promise.all(promises);
      } catch (error) {
        console.error('Error loading profile:', error);
      } finally {
        setLoading(false);
      }
    };

    run();
  }, [targetUserId, currentUser?.id]); // Only depend on user ID to prevent infinite re-renders

  // Update stats when author stats change
  useEffect(() => {
    if (user && authorStats) {
      fetchUserStats(user);
    }
  }, [authorStats, user]);

  const fetchUserData = async () => {
    try {
      if (!targetUserId) return;
      console.log('🔍 fetchUserData called for targetUserId:', targetUserId);
      
      const response = await userApi.getUserById(targetUserId);
      console.log('🔍 getUserById response:', response);
      
      if (response.success) {
        console.log('🔍 User data received:', response.data);
        setUser(response.data);
        // Clear any previous errors
        setErrorType(null);
        setErrorMessage('');
        return response.data;
      } else {
        // Handle specific error cases
        if (response.error === 'account_deleted') {
          setErrorType('account_deleted');
          setErrorMessage(response.message || 'This account has been deleted');
          setUser(null);
        } else if (response.error === 'user_not_found') {
          setErrorType('user_not_found');
          setErrorMessage('User not found');
          setUser(null);
        } else {
          throw new Error(response.error || 'Failed to fetch user');
        }
      }
    } catch (error) {
      message.error('Failed to load user information');
      console.error('Error fetching user:', error);
      setErrorType('general_error');
      setErrorMessage('Failed to load user information');
      setUser(null);
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
      
      const u = userObj || user || {};
      
      console.log('🔍 fetchUserStats called with user:', u);
      console.log('🔍 authorStats from hook:', authorStats);

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

      // Calculate stats from user data if authorStats is not available
      const totalArticles = authorStats?.total_articles || 0;
      const totalViews = authorStats?.total_views || 0;
      const totalLikes = authorStats?.total_likes || 0;

      // Fallback: calculate from user data if hook data is missing
      const fallbackTotalArticles = Array.isArray(u.articles) ? u.articles.length : 0;
      const fallbackTotalViews = u.total_views || u.views || 0;
      const fallbackTotalLikes = u.total_likes || u.likes || 0;

      setStats({
        totalArticles: totalArticles || fallbackTotalArticles,
        totalViews: totalViews || fallbackTotalViews,
        totalLikes: totalLikes || fallbackTotalLikes,
        followers: followersCount,
        following: followingCount
      });

      console.log('📊 User stats updated:', { 
        totalArticles: totalArticles || fallbackTotalArticles,
        totalViews: totalViews || fallbackTotalViews,
        totalLikes: totalLikes || fallbackTotalLikes,
        followers: followersCount,
        following: followingCount,
        userFollowers: u.followers,
        userFollowing: u.following,
        authorStatsAvailable: !!authorStats
      });
    } catch (error) {
      console.error('Error fetching user stats:', error);
    }
  };

  const checkFollowStatus = async () => {
    if (!targetUserId || !isAuthenticated()) {
      console.log('Skip follow status check - not authenticated or no target user');
      setIsFollowing(false);
      return;
    }
    
    try {
      console.log('Checking follow status for user:', targetUserId);
      const response = await userApi.checkFollowStatus(targetUserId);
      console.log('Raw follow status response:', JSON.stringify(response, null, 2));
      
      // Handle different response formats - check all possible nested structures
      let followStatus = false;
      if (response?.data?.data?.is_following !== undefined) {
        followStatus = response.data.data.is_following;
      } else if (response?.data?.is_following !== undefined) {
        followStatus = response.data.is_following;
      } else if (response?.is_following !== undefined) {
        followStatus = response.is_following;
      }
      
      console.log('Parsed follow status:', followStatus);
      setIsFollowing(followStatus);
    } catch (error) {
      console.error('Failed to check follow status:', error);
      console.error('Error details:', error.response?.data || error.message);
      setIsFollowing(false);
    }
  };

  const handleFollow = async () => {
    if (!isAuthenticated()) {
      message.warning('Please log in to follow');
      return;
    }
    
    setFollowLoading(true);
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
    } finally {
      setFollowLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  // Handle error cases
  if (errorType === 'account_deleted') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="bg-white rounded-3xl p-12 shadow-2xl border border-slate-200 text-center max-w-2xl mx-4">
          <div className="w-24 h-24 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <UserOutlined className="text-red-500 text-4xl" />
          </div>
          <h1 className="text-3xl font-bold text-slate-900 mb-4">Account Deleted</h1>
          <p className="text-slate-600 text-lg mb-8">{errorMessage}</p>
          <button
            onClick={() => navigate('/')}
            className="bg-indigo-600 text-white px-8 py-3 rounded-full font-semibold hover:bg-indigo-700 transition-all duration-200"
          >
            Go Home
          </button>
        </div>
      </div>
    );
  }

  if (errorType === 'user_not_found') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="bg-white rounded-3xl p-12 shadow-2xl border border-slate-200 text-center max-w-2xl mx-4">
          <div className="w-24 h-24 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <UserOutlined className="text-yellow-500 text-4xl" />
          </div>
          <h1 className="text-3xl font-bold text-slate-900 mb-4">User Not Found</h1>
          <p className="text-slate-600 text-lg mb-8">{errorMessage}</p>
          <button
            onClick={() => navigate('/')}
            className="bg-indigo-600 text-white px-8 py-3 rounded-full font-semibold hover:bg-indigo-700 transition-all duration-200"
          >
            Go Home
          </button>
        </div>
      </div>
    );
  }

  if (errorType === 'general_error') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="bg-white rounded-3xl p-12 shadow-2xl border border-slate-200 text-center max-w-2xl mx-4">
          <div className="w-24 h-24 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <ExclamationCircleOutlined className="text-red-500 text-4xl" />
          </div>
          <h1 className="text-3xl font-bold text-slate-900 mb-4">Error Loading Profile</h1>
          <p className="text-slate-600 text-lg mb-8">{errorMessage}</p>
          <div className="flex gap-4 justify-center">
            <button
              onClick={() => window.location.reload()}
              className="bg-indigo-600 text-white px-6 py-3 rounded-full font-semibold hover:bg-indigo-700 transition-all duration-200"
            >
              Try Again
            </button>
            <button
              onClick={() => navigate('/')}
              className="bg-gray-600 text-white px-6 py-3 rounded-full font-semibold hover:bg-gray-700 transition-all duration-200"
            >
              Go Home
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <h1>User not found</h1>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-blue-600 text-white relative overflow-hidden">
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="flex flex-col lg:flex-row items-center gap-8">
            {/* Avatar */}
            <div className="relative">
              <div 
                className="w-40 h-40 rounded-full overflow-hidden ring-4 ring-white/20 shadow-2xl cursor-pointer hover:ring-white/40 transition-all duration-200"
                onClick={() => user?.avatar_url && setImageViewerOpen(true)}
              >
                {user?.avatar_url ? (
                  <img 
                    src={user.avatar_url} 
                    alt={user.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full bg-white/20 flex items-center justify-center">
                    <UserOutlined className="text-6xl text-white/70" />
                  </div>
                )}
              </div>
              <div className="absolute -bottom-2 -right-2 w-12 h-12 bg-green-500 rounded-full border-4 border-white flex items-center justify-center">
                <div className="w-3 h-3 bg-white rounded-full animate-pulse"></div>
              </div>
            </div>
            
            {/* User Info */}
            <div className="text-center lg:text-left flex-1">
              <h1 className="text-5xl font-bold mb-3">{user?.name || user?.full_name || user?.username || 'Anonymous'}</h1>
              
              {user?.email && (
                <div className="flex items-center justify-center lg:justify-start gap-2 text-blue-100 mb-3">
                  <MailOutlined className="text-lg" />
                  <span className="text-lg">{user.email}</span>
                </div>
              )}
              
              {(user?.created_at || user?.joined) && (
                <div className="flex items-center justify-center lg:justify-start gap-2 text-blue-100 mb-4">
                  <CalendarOutlined className="text-lg" />
                  <span className="text-lg">
                    Joined {new Date(user.created_at || user.joined).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long', 
                      day: 'numeric'
                    })}
                  </span>
                </div>
              )}
              
              {user?.bio && (
                <p className="text-blue-100 text-xl leading-relaxed mb-6 max-w-2xl">
                  {user.bio}
                </p>
              )}
              
              {/* Followers Info */}
              <div 
                onClick={handleShowFollowers}
                className="flex items-center justify-center lg:justify-start gap-2 text-blue-100 mb-6 cursor-pointer hover:text-white transition-colors"
              >
                <TeamOutlined className="text-lg" />
                <span className="text-lg font-semibold">
                  {stats.followers} Followers
                </span>
              </div>
              
              {/* Action Buttons */}
              <div className="flex gap-4 justify-center lg:justify-start">
                {currentUser?.id === user?.id ? (
                  <button
                    onClick={() => message.info('Edit profile functionality will be developed')}
                    className="bg-white text-indigo-600 px-8 py-3 rounded-full font-semibold hover:bg-blue-50 transition-all duration-200 flex items-center gap-2 shadow-lg"
                  >
                    <EditOutlined />
                    Edit Profile
                  </button>
                ) : (
                  <button
                    onClick={handleFollow}
                    disabled={followLoading}
                    className={`px-8 py-3 rounded-full font-semibold transition-all duration-200 flex items-center gap-2 shadow-lg ${
                      isFollowing 
                        ? 'bg-red-500 hover:bg-red-600 text-white' 
                        : 'bg-white text-indigo-600 hover:bg-blue-50'
                    } ${followLoading ? 'opacity-75 cursor-not-allowed' : ''}`}
                  >
                    {followLoading ? (
                      <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                    ) : (
                      <TeamOutlined />
                    )}
                    {isFollowing ? 'Unfollow' : 'Follow'}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Personal Dashboard Stats - Only show for own profile */}
        {isOwnProfile && (
          <DashboardStats userId={targetUserId} className="mb-16" />
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-16">
          <div className="bg-white rounded-3xl p-8 shadow-xl border border-slate-200 text-center hover:shadow-2xl transition-shadow duration-300">
            <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <FileTextOutlined className="text-indigo-600 text-3xl" />
            </div>
            <div className="text-4xl font-bold text-slate-900 mb-2">{stats.totalArticles}</div>
            <div className="text-slate-600 font-semibold">Articles</div>
          </div>
          
          <div className="bg-white rounded-3xl p-8 shadow-xl border border-slate-200 text-center hover:shadow-2xl transition-shadow duration-300">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <EyeOutlined className="text-green-600 text-3xl" />
            </div>
            <div className="text-4xl font-bold text-slate-900 mb-2">{formatNumber(stats.totalViews)}</div>
            <div className="text-slate-600 font-semibold">Views</div>
          </div>
          
          <div className="bg-white rounded-3xl p-8 shadow-xl border border-slate-200 text-center hover:shadow-2xl transition-shadow duration-300">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <HeartOutlined className="text-red-600 text-3xl" />
            </div>
            <div className="text-4xl font-bold text-slate-900 mb-2">{formatNumber(stats.totalLikes)}</div>
            <div className="text-slate-600 font-semibold">Likes</div>
          </div>
          
          <div 
            onClick={handleShowFollowing}
            className="bg-white rounded-3xl p-8 shadow-xl border border-slate-200 text-center hover:shadow-2xl transition-all duration-300 cursor-pointer hover:scale-105"
          >
            <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <TeamOutlined className="text-yellow-600 text-3xl" />
            </div>
            <div className="text-4xl font-bold text-slate-900 mb-2">{stats.following}</div>
            <div className="text-slate-600 font-semibold">Following</div>
          </div>
        </div>

        {/* Articles Section */}
        <div className="bg-white rounded-3xl shadow-xl border border-slate-200 overflow-hidden">
          <div className="bg-gradient-to-r from-indigo-50 to-purple-50 px-8 py-6 border-b border-slate-200">
            <h2 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
              <div className="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center">
                <FileTextOutlined className="text-white text-xl" />
              </div>
              {(user?.name || user?.full_name || user?.username) ? `${user.name || user.full_name || user.username}'s Articles` : 'Articles'}
            </h2>
            <p className="text-slate-600 text-lg mt-2">
              {stats.totalArticles > 0 
                ? `Discover ${stats.totalArticles} insightful ${stats.totalArticles === 1 ? 'article' : 'articles'}`
                : 'No articles published yet'
              }
            </p>
          </div>
          
          <div className="p-8">
            <ArticleList 
              authorId={user?.id}
              showAuthor={false}
              limit={6}
            />
          </div>
        </div>
      </div>

      {/* Followers Modal */}
      <Modal
        title={`${user?.name || 'User'} - Followers`}
        open={followersModalVisible}
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
                avatar={
                  <div className="w-10 h-10 rounded-full overflow-hidden">
                    {item.avatar_url ? (
                      <img src={item.avatar_url} alt={item.name} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full bg-slate-200 flex items-center justify-center">
                        <UserOutlined className="text-slate-500" />
                      </div>
                    )}
                  </div>
                }
                title={
                  <button 
                    onClick={() => {
                      setFollowersModalVisible(false);
                      navigate(`/profile/${item.id || item._id}`);
                    }}
                    className="text-indigo-600 hover:text-indigo-800 font-semibold"
                  >
                    {item.name || item.full_name}
                  </button>
                }
                description={item.bio || item.email}
              />
            </List.Item>
          )}
        />
      </Modal>

      {/* Following Modal */}
      <Modal
        title={`${user?.name || 'User'} - Following`}
        open={followingModalVisible}
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
                avatar={
                  <div className="w-10 h-10 rounded-full overflow-hidden">
                    {item.avatar_url ? (
                      <img src={item.avatar_url} alt={item.name} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full bg-slate-200 flex items-center justify-center">
                        <UserOutlined className="text-slate-500" />
                      </div>
                    )}
                  </div>
                }
                title={
                  <button 
                    onClick={() => {
                      setFollowingModalVisible(false);
                      navigate(`/profile/${item.id || item._id}`);
                    }}
                    className="text-indigo-600 hover:text-indigo-800 font-semibold"
                  >
                    {item.name || item.full_name}
                  </button>
                }
                description={item.bio || item.email}
              />
            </List.Item>
          )}
        />
      </Modal>

      {/* Image Viewer Modal */}
      {imageViewerOpen && (
        <div 
          className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
          onClick={() => setImageViewerOpen(false)}
        >
          <div className="relative max-w-4xl max-h-full">
            <img 
              src={user?.avatar_url}
              alt={user?.name || 'User Avatar'}
              className="max-w-full max-h-full object-contain rounded-lg shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            />
            <button
              onClick={() => setImageViewerOpen(false)}
              className="absolute top-4 right-4 w-10 h-10 bg-black/50 hover:bg-black/70 rounded-full flex items-center justify-center text-white transition-colors"
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Profile;
