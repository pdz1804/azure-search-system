/* eslint-disable */
/* @ts-nocheck */
/* JAF-ignore */
import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Layout, 
  Typography, 
  Tag, 
  Button, 
  Space, 
  Avatar, 
  Divider, 
  message,
  Spin,
  Card,
  Modal,
  Row,
  Col,
  Image
} from 'antd';
import { 
  ArrowLeftOutlined,
  EyeOutlined, 
  LikeOutlined, 
  DislikeOutlined,
  EditOutlined,
  DeleteOutlined,
  UserAddOutlined,
  UserDeleteOutlined,
  ExclamationCircleOutlined,
  HeartOutlined,
  BookOutlined,
  ClockCircleOutlined,
  UserOutlined
} from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { articleApi } from '../api/articleApi';
import { userApi } from '../api/userApi';
import { useAuth } from '../context/AuthContext';
import { formatDate, formatNumber } from '../utils/helpers';
import { getRandomDefaultImage } from '../utils/defaultImage';
import { clearArticleListCache } from '../components/ArticleList';

const { Content } = Layout;
const { Title, Text, Paragraph } = Typography;
const { confirm } = Modal;

// Module-level caches to dedupe and avoid repeated network fetches during dev (StrictMode)
const ARTICLE_CACHE = new Map();
const ARTICLE_FETCH_PROMISES = new Map();

const ArticleDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, isAuthenticated, canEditArticle, refreshUser } = useAuth();
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isFollowing, setIsFollowing] = useState(false);
  const [likeLoading, setLikeLoading] = useState(false);
  const [dislikeLoading, setDislikeLoading] = useState(false);
  const [bookmarkLoading, setBookmarkLoading] = useState(false);
  const [followLoading, setFollowLoading] = useState(false);
  const [reactionType, setReactionType] = useState('none');
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [showMoreRecommendations, setShowMoreRecommendations] = useState(false);
  const [top5Recommendations, setTop5Recommendations] = useState([]);
  const [more5Recommendations, setMore5Recommendations] = useState([]);
  const [recommendationsLoading, setRecommendationsLoading] = useState(false);
  const [recommendationsUpdatedAt, setRecommendationsUpdatedAt] = useState(null);
  const [refreshCountdown, setRefreshCountdown] = useState(0);
  const [recommendedAuthors, setRecommendedAuthors] = useState([]);
  const [recommendationCountdown, setRecommendationCountdown] = useState(null);

  // Memoized recommendation processing to avoid infinite loops
  const processedRecommendations = React.useMemo(() => {
    const backendRecommendations = article?.recommended || article?.recommendations || [];
    
    if (!Array.isArray(backendRecommendations)) {
      return [];
    }
    
    // Check if we have full article objects or just ID/score objects
    const processed = backendRecommendations.map(rec => {
      // If it's just an ID/score object, we can't display it properly
      if (rec.article_id && !rec.title) {
        console.warn('Recommendation contains only ID, not full article data:', rec);
        return null;
      }
      // If it's a full article object, use it as is
      return rec;
    }).filter(Boolean); // Remove null entries
    
    // console.log('Processing recommendations:', processed.length, 'valid recommendations');
    return processed;
  }, [article?.recommended, article?.recommendations]);

  const recommendations = React.useMemo(() => {
    return {
      top5: processedRecommendations.slice(0, 5),
      more5: processedRecommendations.slice(5, 10),
      total: processedRecommendations.length,
      was_refreshed: processedRecommendations.length > 0,
      last_updated: article?.recommended_time || null
    };
  }, [processedRecommendations, article?.recommended_time]);
    
  const top5Recs = recommendations.top5;
  const more5Recs = recommendations.more5;
  const totalRecommendations = recommendations.total;
  const wasRefreshed = recommendations.was_refreshed;
  const lastUpdated = recommendations.last_updated;

  // Format countdown display
  const formatCountdown = (seconds) => {
    if (seconds <= 0) return 'Refreshing...';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  // Format display date for recommendations
  const formatDisplayDate = (dateStr) => {
    if (!dateStr) return 'Unknown';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      return 'Invalid date';
    }
  };

  // per-recommendation follow button removed; keep global follow handling via handleFollow

  const handleBookmarkRec = async (articleId) => {
    if (!isAuthenticated()) {
      message.warning('Please login to bookmark');
      return;
    }
    try {
      await userApi.bookmarkArticle(articleId);
      message.success('Bookmarked');
    } catch (e) {
      message.error('Failed to bookmark');
    }
  };

  useEffect(() => {
    let mounted = true;
    
    if (id && mounted) {
      fetchArticle();
      if (isAuthenticated()) {
        loadUserReactionStatus();
      }
    }
    
    return () => {
      mounted = false;
    };
  }, [id]);

  // Separate useEffect to load reaction status when user data changes
  useEffect(() => {
    if (id && isAuthenticated() && user) {
      loadUserReactionStatus();
    }
  }, [user, id]); // Load reaction status when user data becomes available

  // Separate useEffect to check follow status when user and article are ready
  useEffect(() => {
    if (article && user && isAuthenticated()) {
      const authorId = article.author_id || article.author?.id;
      console.log('useEffect checkFollow - authorId:', authorId, 'userId:', user.id || user.user_id);
      
      if (authorId && authorId !== user.id && authorId !== user.user_id) {
        console.log('Calling checkFollowStatus from useEffect for author:', authorId);
        checkFollowStatus(authorId);
      } else {
        console.log('Skipping follow check - same user or missing data');
      }
    }
  }, [article, user]); // Check follow status when article and user data are available

  useEffect(() => {
    if (top5Recs.length > 0) {
      setTop5Recommendations(top5Recs);
      setMore5Recommendations(more5Recs);
      if (lastUpdated) {
        setRecommendationsUpdatedAt(lastUpdated);
        // Set initial countdown (60 minutes = 3600 seconds)
        const updateTime = new Date(lastUpdated);
        const now = new Date();
        const elapsed = Math.floor((now - updateTime) / 1000);
        const remaining = Math.max(0, 3600 - elapsed); // 60 minutes
        setRefreshCountdown(remaining);
        console.log(`⏰ Timer initialized: last_updated=${lastUpdated}, elapsed=${elapsed}s, remaining=${remaining}s`);
      } else {
        console.log('⚠️ No recommended_time from backend, timer not initialized');
        setRefreshCountdown(0); // No timer if no timestamp
      }
    } else {
      console.log('📋 No recommendations available, resetting timer');
      setRefreshCountdown(0);
    }
  }, [top5Recs, more5Recs, lastUpdated]);

  // Countdown timer effect
  useEffect(() => {
    if (refreshCountdown > 0) {
      const timer = setTimeout(() => {
        setRefreshCountdown(refreshCountdown - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else if (refreshCountdown === 0 && recommendationsUpdatedAt) {
      // Auto-refresh recommendations when countdown reaches 0
      fetchRecommendations();
    }
  }, [refreshCountdown, recommendationsUpdatedAt]);

  // Refresh just the article/recommendations by reusing fetchArticle
  const fetchRecommendations = async () => {
    try {
      await fetchArticle();
    } catch (e) {
      console.error('Failed to refresh recommendations:', e);
    }
  };

  const fetchArticle = async () => {
    try {
      setLoading(true);
      console.log('Fetching article with ID:', id);

      let response = null;

      // Use module-level cache to avoid duplicate fetches triggered by React StrictMode
      if (ARTICLE_CACHE.has(id)) {
        const cached = ARTICLE_CACHE.get(id);
        setArticle(cached);
        response = { success: true, data: cached };
      } else if (ARTICLE_FETCH_PROMISES.has(id)) {
        // Wait for existing in-flight request
        response = await ARTICLE_FETCH_PROMISES.get(id);
        if (response && response.success) {
          ARTICLE_CACHE.set(id, response.data);
          setArticle(response.data);
        }
      } else {
        const promise = articleApi.getArticle(id);
        ARTICLE_FETCH_PROMISES.set(id, promise);
        response = await promise;
        ARTICLE_FETCH_PROMISES.delete(id);
        if (response && response.success) {
          ARTICLE_CACHE.set(id, response.data);
          setArticle(response.data);
        }
      }

      if (response && response.success) {
        const data = response.data;
        
        // Debug: Log the recommended_time field from backend
        console.log('🔍 Backend response debug:', {
          hasRecommended: !!data.recommended,
          recommendedCount: Array.isArray(data.recommended) ? data.recommended.length : 0,
          recommendedTime: data.recommended_time,
          recommendedTimeType: typeof data.recommended_time
        });
        
        // Recommendations are now included directly in the article data
        if (data.recommendations) {
          if (data.recommendations.was_refreshed) {
            console.log('📋 Recommendations were refreshed from backend');
          } else {
            console.log('💾 Using cached recommendations from backend');
          }
        }
        
        // Check follow status if user is logged in and not the author
        const authorId = data?.author_id || data?.author?.id;
        console.log('Checking follow conditions:', {
          isAuthenticated: isAuthenticated(),
          authorId: authorId,
          userId: user?.id,
          userIdFromAuth: user?.user_id,
          shouldCheckFollow: isAuthenticated() && authorId && authorId !== user?.id && authorId !== user?.user_id
        });
        
        if (isAuthenticated() && authorId && authorId !== user?.id && authorId !== user?.user_id) {
          console.log('Calling checkFollowStatus for author:', authorId);
          checkFollowStatus(authorId);
        } else {
          console.log('Skipping follow status check - conditions not met');
        }
      } else {
        console.error('Article API returned error:', response?.error);
        message.error(response?.error || 'Cannot load article');
        navigate('/');
      }
    } catch (error) {
      console.error('Error fetching article:', error);
      message.error('Cannot load article');
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  // Recommendations are now loaded directly from the backend via the article API
  // No separate fetching needed - they come with the article data

  useEffect(() => {
    // Load popular authors: top 5 authors with most followers/articles/views in current app (excluding current article author)
    const loadRecommendedAuthors = async () => {
      try {
        console.log('🔍 Starting loadRecommendedAuthors...');
        
        // Fix: Backend returns author_id and author_name as separate fields, not nested under author object
        const authorId = article?.author_id || article?.author?.id;
        const authorName = article?.author_name || article?.author?.name;
        
        console.log('📄 Article data:', {
          hasArticle: !!article,
          authorId: authorId,
          authorName: authorName,
          appId: article?.app_id
        });
        
        if (!authorId) {
          console.log('❌ No article author ID found, skipping popular authors load');
          return;
        }
        
        console.log('📞 Calling userApi.getAllUsers...');
        const usersResp = await userApi.getAllUsers(1, 100);
        console.log('📥 Users API response:', {
          success: usersResp.success,
          dataType: typeof usersResp.data,
          hasItems: !!usersResp.data?.items,
          hasData: !!usersResp.data,
          dataLength: usersResp.data?.items?.length || usersResp.data?.length || 0
        });
        
        if (usersResp.success) {
          const items = usersResp.data?.items || usersResp.data || [];
          console.log('👥 Raw user data sample:', items.slice(0, 2));
          console.log('📊 Total users returned:', items.length);
          
          // Filter out the current article author and inactive users
          const filteredUsers = items.filter(user => 
            user.user_id !== authorId && user.is_active !== false
          );
          console.log('🔍 Users after filtering:', {
            total: items.length,
            filtered: filteredUsers.length,
            currentAuthorId: authorId,
            filteredOut: items.length - filteredUsers.length
          });
          
          // Sort by total_followers first, then by total_articles, then by total_views
          const top = filteredUsers
            .sort((a, b) => {
              const aScore = (a.total_followers || 0) * 10000 + (a.total_articles || 0) * 100 + (a.total_views || 0);
              const bScore = (b.total_followers || 0) * 10000 + (b.total_articles || 0) * 100 + (b.total_views || 0);
              return bScore - aScore;
            })
            .slice(0, 5);
            
          console.log('🏆 Top 5 popular authors:', top.map(u => ({
            name: u.full_name,
            followers: u.total_followers,
            articles: u.articles_count,
            views: u.total_views
          })));
          console.log('📝 Sample user structure:', items[0]);
          setRecommendedAuthors(top);
        } else {
          console.error('❌ Users API call failed:', usersResp);
        }
      } catch (e) {
        console.error('💥 Failed to load recommended authors:', e);
        
        // Even if the main API fails, try to get authors from recommended articles as fallback
        try {
          console.log('🔄 Trying fallback to recommended article authors...');
          if (article.recommended && Array.isArray(article.recommended)) {
            const fallbackAuthors = article.recommended
              .filter(rec => {
                // Fix: Check for author_id or author.id
                const recAuthorId = rec.author_id || rec.author?.id;
                return recAuthorId && recAuthorId !== (article?.author_id || article?.author?.id);
              })
              .map(rec => ({
                user_id: rec.author_id || rec.author?.id,
                full_name: rec.author_name || rec.author?.name || rec.author?.full_name || 'Unknown Author',
                avatar_url: rec.author?.avatar_url,
                role: rec.author?.role || 'user',
                is_active: true,
                articles_count: 1,
                total_views: rec.total_view || rec.views || 0,
                total_followers: 0
              }))
              .slice(0, 5);
            
            if (fallbackAuthors.length > 0) {
              console.log('✅ Using fallback authors from recommended articles:', fallbackAuthors);
              setRecommendedAuthors(fallbackAuthors);
            } else {
              console.log('⚠️ No fallback authors found in recommended articles');
            }
          } else {
            console.log('⚠️ No recommended articles available for fallback');
          }
        } catch (fallbackError) {
          console.error('💥 Fallback also failed:', fallbackError);
        }
      }
    };
    loadRecommendedAuthors();
  }, [article?.author?.id]);

  // Debug logging only when article changes
  useEffect(() => {
    if (article) {
      // console.log('Article loaded:', {
      //   id: article.id,
      //   title: article.title,
      //   hasContent: !!article.content,
      //   hasAbstract: !!article.abstract,
      //   hasRecommended: !!article.recommended,
      //   recommendedCount: Array.isArray(article.recommended) ? article.recommended.length : 0
      // });
    }
  }, [article?.id, article?.recommended?.length]);

  const loadUserReactionStatus = async () => {
    try {
      console.log('loadUserReactionStatus called with user:', user);
      console.log('Article ID:', id);
      
      if (!user) {
        console.log('No user data available yet, setting defaults');
        setReactionType('none');
        setIsBookmarked(false);
        return;
      }
      
      // First check user data for immediate feedback
      const userLikedArticles = user?.liked_articles || [];
      const userDislikedArticles = user?.disliked_articles || [];
      const userBookmarkedArticles = user?.bookmarked_articles || [];
      
      const isLiked = userLikedArticles.includes(id);
      const isDisliked = userDislikedArticles.includes(id);
      const isBookmarked = userBookmarkedArticles.includes(id);
      
      // Set initial state from user data
      setReactionType(isLiked ? 'like' : isDisliked ? 'dislike' : 'none');
      setIsBookmarked(isBookmarked);
      
      console.log('Loaded reaction status from user data:', {
        isLiked,
        isDisliked, 
        isBookmarked,
        userLikedArticles,
        userBookmarkedArticles,
        reactionType: isLiked ? 'like' : isDisliked ? 'dislike' : 'none'
      });
      
      // Try to get updated status from API as well (optional enhancement)
      try {
        const res = await userApi.checkArticleReactionStatus(id);
        if (res.success) {
          const { reaction_type, is_bookmarked } = res.data;
          setReactionType(reaction_type || 'none');
          setIsBookmarked(is_bookmarked || false);
          console.log('Updated reaction status from API:', { reaction_type, is_bookmarked });
        }
      } catch (apiError) {
        console.log('API status check failed, using user data:', apiError.message);
        // Keep the values from user data
      }
    } catch (error) {
      console.error('Error loading user reaction status:', error);
      // Set default values on error
      setReactionType('none');
      setIsBookmarked(false);
    }
  };

  const checkFollowStatus = async (authorId) => {
    console.log('checkFollowStatus called with authorId:', authorId);
    try {
      console.log('Making API call to check follow status...');
      const response = await userApi.checkFollowStatus(authorId);
      console.log('Follow status response:', response);
      const followStatus = response.data?.is_following || false;
      console.log('Setting isFollowing to:', followStatus);
      setIsFollowing(followStatus);
    } catch (error) {
      console.error('Error checking follow status:', error);
      setIsFollowing(false);
    }
  };

  const handleLike = async () => {
    if (!isAuthenticated()) {
      message.warning('Please login to like articles');
      return;
    }
    const prevType = reactionType; // capture previous reaction
    
    try {
      setLikeLoading(true);
      let response;
      
      if (prevType === 'like') {
        response = await userApi.unlikeArticle(id);
        if (response.success) {
          setReactionType('none');
          message.success('Article unliked');
          // adjust counts locally
          setArticle(prev => ({
            ...prev,
            likes: (prev.likes || prev.total_like || 1) - 1
          }));
        }
      } else {
        if (prevType === 'dislike') {
          await userApi.undislikeArticle(id);
        }
        response = await userApi.likeArticle(id);
        if (response.success) {
          setReactionType('like');
          message.success('Article liked');
          // adjust counts locally
          setArticle(prev => ({
            ...prev,
            likes: (prev.likes || prev.total_like || 0) + 1,
            dislikes: prevType === 'dislike' ? (prev.dislikes || prev.total_dislike || 1) - 1 : (prev.dislikes || prev.total_dislike)
          }));
        }
      }
      
      if (response?.success) {
        // update cache too
        try {
          const articleResponse = await articleApi.getArticle(id);
          if (articleResponse.success) {
            setArticle(articleResponse.data);
            ARTICLE_CACHE.set(id, articleResponse.data);
          }
          await loadUserReactionStatus();
          // Refresh user data to update liked_articles array for other components
          await refreshUser();
          // Clear article list cache to ensure updated reactions show in lists
          clearArticleListCache();
        } catch (refreshError) {
          console.error('Error refreshing article data:', refreshError);
          // Fallback to full refresh if quick refresh fails
          await fetchArticle();
        }
      }
    } catch (error) {}
    finally {
      setLikeLoading(false);
    }
  };

  const handleDislike = async () => {
    if (!isAuthenticated()) {
      message.warning('Please login to dislike articles');
      return;
    }
    const prevType = reactionType;

    try {
      setDislikeLoading(true);
      let response;

      if (prevType === 'dislike') {
        response = await userApi.undislikeArticle(id);
        if (response.success) {
          setReactionType('none');
          message.success('Article undisliked');
          setArticle(prev => ({
            ...prev,
            dislikes: (prev.dislikes || prev.total_dislike || 1) - 1
          }));
        }
      } else {
        if (prevType === 'like') {
          await userApi.unlikeArticle(id);
        }
        response = await userApi.dislikeArticle(id);
        if (response.success) {
          setReactionType('dislike');
          message.success('Article disliked');
          setArticle(prev => ({
            ...prev,
            dislikes: (prev.dislikes || prev.total_dislike || 0) + 1,
            likes: prevType === 'like' ? (prev.likes || prev.total_like || 1) - 1 : (prev.likes || prev.total_like)
          }));
        }
      }

      if (response?.success) {
        try {
          const articleResponse = await articleApi.getArticle(id);
          if (articleResponse.success) {
            setArticle(articleResponse.data);
            ARTICLE_CACHE.set(id, articleResponse.data);
          }
          await loadUserReactionStatus();
          // Refresh user data to update disliked_articles array for other components
          await refreshUser();
          // Clear article list cache to ensure updated reactions show in lists
          clearArticleListCache();
        } catch (refreshError) {
          await fetchArticle();
        }
      }
    } catch (error) {}
    finally {
      setDislikeLoading(false);
    }
  };

  const toggleBookmark = async () => {
    if (!isAuthenticated()) {
      message.warning('Please login to bookmark articles');
      return;
    }
    setBookmarkLoading(true);
    try {
      if (isBookmarked) {
        const res = await userApi.unbookmarkArticle(id);
        if (res.success) {
          setIsBookmarked(false);
          // Refresh user data to update bookmarked_articles array for other components
          await refreshUser();
          // Clear article list cache to ensure updated bookmarks show in lists
          clearArticleListCache();
        }
      } else {
        const res = await userApi.bookmarkArticle(id);
        if (res.success) {
          setIsBookmarked(true);
          // Refresh user data to update bookmarked_articles array for other components
          await refreshUser();
          // Clear article list cache to ensure updated bookmarks show in lists
          clearArticleListCache();
        }
      }
    } catch {
      message.error('Failed to update bookmark status');
    } finally {
      setBookmarkLoading(false);
    }
  };

  const handleFollow = async () => {
    if (!isAuthenticated()) {
      message.warning('Please login to follow authors');
      return;
    }
    
    const authorId = article.author_id || article.author?.id;
    if (!authorId) {
      message.error('Author information not available');
      return;
    }
    
    setFollowLoading(true);
    try {
      if (isFollowing) {
        await userApi.unfollowUser(authorId);
        message.success('Unfollowed');
        setIsFollowing(false);
      } else {
        await userApi.followUser(authorId);
        message.success('Followed');
        setIsFollowing(true);
      }
    } catch (error) {
      console.error('Follow/unfollow error:', error);
      message.error('Failed to perform action');
    } finally {
      setFollowLoading(false);
    }
  };

  const handleEdit = () => {
    navigate(`/write/${id}`);
  };

  const handleDelete = () => {
    confirm({
      title: 'Are you sure you want to delete this article?',
      icon: React.createElement(ExclamationCircleOutlined),
      content: 'This article will be permanently deleted.',
      okText: 'Delete',
      okType: 'danger',
      cancelText: 'Cancel',
      async onOk() {
        try {
          await articleApi.deleteArticle(id);
          message.success('Article deleted successfully');
          navigate('/');
        } catch (error) {
          message.error('Failed to delete article');
        }
      },
    });
  };

  if (loading) {
    return (
      <Layout style={{ minHeight: '100vh' }}>
        <Content style={{ padding: '24px' }}>
          <div style={{ maxWidth: 1200, margin: '0 auto', textAlign: 'center' }}>
        <Spin size="large" />
            <div style={{ marginTop: 16, color: '#666' }}>Loading article...</div>
      </div>
        </Content>
      </Layout>
    );
  }

  if (!article) {
    return (
      <Layout style={{ minHeight: '100vh' }}>
        <Content style={{ padding: '24px' }}>
          <div style={{ maxWidth: 1200, margin: '0 auto', textAlign: 'center' }}>
            <Title level={2} style={{ color: '#666' }}>Article not found</Title>
            <Text type="secondary">The article you're looking for doesn't exist or has been removed.</Text>
      </div>
        </Content>
      </Layout>
    );
  }



  const calculateReadingTime = (content) => {
    if (!content || typeof content !== 'string') return 1; // Default to 1 min if no content
    const words = content.trim().split(/\s+/).filter(word => word.length > 0).length;
    const readingSpeed = 200; // Average words per minute
    return Math.max(1, Math.ceil(words / readingSpeed)); // Minimum 1 minute
  };
  
  // Get content for reading time calculation (fallback to abstract if content is missing)
  const contentForReading = article.content || article.abstract || '';

  // Handle both backend field names for compatibility
  // Use nullish coalescing so counts use updated values even if 0
  const likesCount = article.likes ?? article.total_like ?? 0;
  const dislikesCount = article.dislikes ?? article.total_dislike ?? 0;
  const viewsCount = article.views || article.total_view || 0;
  
  // Extract author info from backend structure
  const authorName = article.author_name || article.author?.name || 'Unknown Author';
  const authorId = article.author_id || article.author?.id;
  const authorAvatar = article.author_avatar_url || article.author?.avatar_url;

  // Debug: Removed to prevent infinite loop
  // React.useEffect(() => {
  //   if (article && user) {
  //     console.log('Follow button visibility check:', {
  //       isAuthenticated: isAuthenticated(),
  //       authorId: authorId,
  //       userId: user?.id,
  //       userIdFromAuth: user?.user_id,
  //       showFollowButton: isAuthenticated() && authorId && 
  //                        authorId !== user?.id && 
  //                        authorId !== user?.user_id
  //     });
  //   }
  // }, [article?.id, user?.id, authorId]);

  // Custom components for markdown rendering
  const markdownComponents = {
    code({ node, inline, className, children, ...props }) {
      const match = /language-(\w+)/.exec(className || '');
      return !inline && match ? (
        <SyntaxHighlighter
          style={tomorrow}
          language={match[1]}
          PreTag="div"
          {...props}
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      ) : (
        <code className={className} {...props}>
          {children}
        </code>
      );
    },
    h1: ({ children }) => <Title level={1}>{children}</Title>,
    h2: ({ children }) => <Title level={2}>{children}</Title>,
    h3: ({ children }) => <Title level={3}>{children}</Title>,
    h4: ({ children }) => <Title level={4}>{children}</Title>,
    h5: ({ children }) => <Title level={5}>{children}</Title>,
    h6: ({ children }) => <Title level={6}>{children}</Title>,
    p: ({ children }) => <Paragraph style={{ marginBottom: 16 }}>{children}</Paragraph>,
    ul: ({ children }) => <ul style={{ marginBottom: 16, paddingLeft: 20 }}>{children}</ul>,
    ol: ({ children }) => <ol style={{ marginBottom: 16, paddingLeft: 20 }}>{children}</ol>,
    li: ({ children }) => <li style={{ marginBottom: 8 }}>{children}</li>,
    blockquote: ({ children }) => (
      <blockquote style={{ 
        borderLeft: '4px solid #1890ff', 
        paddingLeft: 16, 
        margin: '16px 0',
        fontStyle: 'italic',
        color: '#666'
      }}>
        {children}
      </blockquote>
    ),
    strong: ({ children }) => <strong style={{ fontWeight: 600 }}>{children}</strong>,
    em: ({ children }) => <em style={{ fontStyle: 'italic' }}>{children}</em>,
    a: ({ href, children }) => (
      <a href={href} target="_blank" rel="noopener noreferrer" style={{ color: '#1890ff' }}>
        {children}
      </a>
    ),
  };

  return (
    <Layout style={{ minHeight: '100vh', background: '#f8f9fa' }}>
      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <Row gutter={24}>
            {/* Left Column - Article Content */}
            <Col xs={24} lg={16}>
              {/* Article Header */}
              <Card 
                style={{ 
                  marginBottom: 24, 
                  borderRadius: 16,
                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                  border: 'none'
                }}
              >
                <div style={{ marginBottom: 24 }}>
                  <Title level={1} style={{ marginBottom: 16, color: '#1a1a1a' }}>
                    {article.title}
                  </Title>
                  
                  {/* Tags */}
                  {article.tags && article.tags.length > 0 && (
                    <div style={{ marginBottom: 16 }}>
                      <Space wrap>
                        {article.tags.map((tag, index) => (
                          <Tag 
                            key={index} 
                            color="blue" 
                            style={{ 
                              borderRadius: 16, 
                              padding: '4px 12px',
                              fontSize: 12
                            }}
                          >
                            {tag}
                          </Tag>
                        ))}
                      </Space>
                    </div>
                  )}
                  
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: 16, 
                    marginBottom: 16,
                    flexWrap: 'wrap'
                  }}>
                    <Avatar 
                      size={48} 
                      src={authorAvatar}
                      style={{ cursor: 'pointer' }}
                      onClick={() => navigate(`/profile/${authorId}`)}
                    >
                      {authorName?.[0] || 'A'}
                    </Avatar>
                    
                    <div style={{ flex: 1 }}>
                      <Text 
                        strong 
                        style={{ 
                          fontSize: 16, 
                          cursor: 'pointer',
                          color: '#1890ff'
                        }}
                        onClick={() => navigate(`/profile/${authorId}`)}
                      >
                        {authorName}
                      </Text>
                      <br />
                      <Space size={16}>
                        <Text type="secondary" style={{ fontSize: 14 }}>
                          <ClockCircleOutlined style={{ marginRight: 4 }} />
                          {formatDate(article.created_at || article.created_date)}
                        </Text>
                        <Text type="secondary" style={{ fontSize: 14 }}>
                          <EyeOutlined style={{ marginRight: 4 }} />
                          {calculateReadingTime(contentForReading)} min read
                        </Text>
                        {viewsCount > 0 && (
                          <Text type="secondary" style={{ fontSize: 14 }}>
                            <EyeOutlined style={{ marginRight: 4 }} />
                            {formatNumber(viewsCount)} views
                          </Text>
                        )}
                      </Space>
                    </div>
                  </div>

                  {/* Featured Image */}
                  {article.image && (
                    <div style={{ marginBottom: 16 }}>
                      <Image
                        src={article.image}
                        alt={article.title}
                        style={{ 
                          width: '100%', 
                          maxHeight: 400, 
                          objectFit: 'cover',
                          borderRadius: 8
                        }}
                        fallback={getRandomDefaultImage()}
                      />
                    </div>
                  )}

                  {article.abstract && (
                    <div style={{ 
                      padding: 16, 
                      background: '#f0f8ff', 
                      borderRadius: 8, 
                      borderLeft: '4px solid #1890ff',
                      marginBottom: 16
                    }}>
                      <Text style={{ fontSize: 16, color: '#1a1a1a' }}>
                        {article.abstract}
                      </Text>
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div style={{ 
                  display: 'flex', 
                  gap: 12, 
                  flexWrap: 'wrap',
                  borderTop: '1px solid #f0f0f0',
                  paddingTop: 16
                }}>
                  <Button
                    type={reactionType === 'like' ? 'primary' : 'default'}
                    icon={<HeartOutlined />}
                    onClick={handleLike}
                    loading={likeLoading}
                    style={{ 
                      borderRadius: 20,
                      height: 40,
                      paddingLeft: 20,
                      paddingRight: 20
                    }}
                  >
                    {reactionType === 'like' ? 'Liked' : 'Like'} ({likesCount})
                  </Button>

                  <Button
                    type={reactionType === 'dislike' ? 'primary' : 'default'}
                    icon={<DislikeOutlined />}
                    onClick={handleDislike}
                    loading={dislikeLoading}
                    style={{ 
                      borderRadius: 20,
                      height: 40,
                      paddingLeft: 20,
                      paddingRight: 20
                    }}
                  >
                    {reactionType === 'dislike' ? 'Disliked' : 'Dislike'} ({dislikesCount})
                  </Button>

                  <Button
                    type={isBookmarked ? 'primary' : 'default'}
                    icon={<BookOutlined />}
                    onClick={toggleBookmark}
                    loading={bookmarkLoading}
                    style={{ 
                      borderRadius: 20,
                      height: 40,
                      paddingLeft: 20,
                      paddingRight: 20
                    }}
                  >
                    {isBookmarked ? 'Bookmarked' : 'Bookmark'}
                  </Button>
                
                {isAuthenticated() && authorId && 
                 authorId !== user?.id && 
                 authorId !== user?.user_id && (
                  <Button
                    type={isFollowing ? "primary" : "default"}
                    icon={isFollowing ? <UserDeleteOutlined /> : <UserAddOutlined />}
                    onClick={handleFollow}
                    loading={followLoading}
                      style={{ 
                        borderRadius: 20,
                        height: 40,
                        paddingLeft: 20,
                        paddingRight: 20
                      }}
                    >
                      {isFollowing ? 'Unfollow' : 'Follow'}
                  </Button>
                )}

                {canEditArticle(article) && (
                  <>
                    <Button
                      icon={<EditOutlined />}
                      onClick={handleEdit}
                        style={{ 
                          borderRadius: 20,
                          height: 40,
                          paddingLeft: 20,
                          paddingRight: 20
                        }}
                      >
                        Edit
                    </Button>
                    <Button
                      danger
                      icon={<DeleteOutlined />}
                      onClick={handleDelete}
                        style={{ 
                          borderRadius: 20,
                          height: 40,
                          paddingLeft: 20,
                          paddingRight: 20
                        }}
                      >
                        Delete
                    </Button>
                  </>
                )}
                </div>
              </Card>

              {/* Article Content */}
              <Card 
                style={{ 
                  borderRadius: 16,
                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                  border: 'none'
                }}
              >
                <div 
                  className="article-content"
                  style={{ 
                    fontSize: 16, 
                    lineHeight: 1.8, 
                    color: '#1a1a1a',
                    padding: '24px 0'
                  }}
                >
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeRaw]}
                    components={markdownComponents}
                  >
                    {article.content}
                  </ReactMarkdown>
                </div>
              </Card>
            </Col>

            {/* Right Column - Recommendations */}
            <Col xs={24} lg={8}>
              <div style={{ position: 'sticky', top: 100 }}>
                <Card 
                  title={
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <BookOutlined style={{ color: '#1890ff' }} />
                        <span>Recommended Articles</span>
                        {totalRecommendations > 0 && (
                          <Tag color="blue" style={{ marginLeft: 4 }}>
                            {totalRecommendations}
                          </Tag>
                        )}
                      </div>
                      {wasRefreshed && (
                        <Tag color="green" size="small">
                          ✨ Fresh
                        </Tag>
                      )}
                    </div>
                  }
                  extra={
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
                      {lastUpdated ? (
                        <>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            <ClockCircleOutlined style={{ marginRight: 4 }} />
                            {formatDisplayDate(lastUpdated)}
                          </Text>
                          {refreshCountdown > 0 && (
                            <Text type="secondary" style={{ fontSize: 11, color: '#52c41a' }}>
                              Refresh in {formatCountdown(refreshCountdown)}
                            </Text>
                          )}
                        </>
                      ) : (
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          <ClockCircleOutlined style={{ marginRight: 4 }} />
                          No timestamp available
                        </Text>
                      )}
                    </div>
                  }
                  style={{ 
                    borderRadius: 16,
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                    border: 'none'
                  }}
                >
                  {recommendationsLoading ? (
                    <div style={{ textAlign: 'center', padding: '20px' }}>
                      <Spin />
                    </div>
                  ) : top5Recommendations.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                      {top5Recommendations.map((rec) => {
                        return (
                          <Card key={rec.id} size="small" hoverable style={{ borderRadius: 8 }}>
                            <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                              {rec.image ? (
                                <Image src={rec.image} alt={rec.title} width={72} height={56} style={{ objectFit: 'cover', borderRadius: 6 }} />
                              ) : (
                                <div style={{ width: 72, height: 56, background: '#f0f0f0', borderRadius: 6 }} />
                              )}

                              <div style={{ flex: 1, minWidth: 0 }}>
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                                  <Text strong style={{ fontSize: 14, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{rec.title}</Text>
                                </div>
                                <div style={{ marginTop: 6 }}>
                                  <Text type="secondary" style={{ fontSize: 12 }}><UserOutlined /> {rec.author?.name || rec.author || 'Unknown Author'}</Text>
                                </div>
                                <div style={{ marginTop: 8, display: 'flex', gap: 8, alignItems: 'center' }}>
                                  <Button type="primary" size="small" onClick={() => {
                                    const recId = rec.id || rec.article_id;
                                    console.log('Navigating to recommendation:', { rec, recId });
                                    if (recId) {
                                      navigate(`/articles/${recId}`);
                                    } else {
                                      console.error('No ID found for recommendation:', rec);
                                    }
                                  }}>Read</Button>
                                  <Button size="small" shape="default" onClick={() => {
                                    const recId = rec.id || rec.article_id;
                                    if (recId) {
                                      handleBookmarkRec(recId);
                                    }
                                  }} style={{ marginLeft: 4 }}>
                                    <BookOutlined />
                                  </Button>
                                </div>
                              </div>
                            </div>
                          </Card>
                        );
                      })}

                      {more5Recommendations.length > 0 && (
                        <div style={{ display: 'flex', justifyContent: 'center', marginTop: 8 }}>
                          <Button type="link" onClick={() => setShowMoreRecommendations(true)}>Show more ({more5Recommendations.length})</Button>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
                      <BookOutlined style={{ fontSize: 24, marginBottom: 8 }} />
                      <div>No recommendations yet</div>
                    </div>
                  )}
                </Card>

                {/* Show More Modal for additional recommendations */}
                <Modal
                  title="More Recommendations"
                  open={showMoreRecommendations}
                  onCancel={() => setShowMoreRecommendations(false)}
                  footer={null}
                  width={720}
                >
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {more5Recommendations && more5Recommendations.length > 0 ? (
                      more5Recommendations.map(rec => (
                        <Card key={rec.id} size="small" hoverable style={{ borderRadius: 8 }} bodyStyle={{ padding: 12 }}>
                          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                            {rec.image ? (
                              <Image src={rec.image} alt={rec.title} width={72} height={56} style={{ objectFit: 'cover', borderRadius: 6 }} />
                            ) : (
                              <div style={{ width: 72, height: 56, background: '#f0f0f0', borderRadius: 6 }} />
                            )}
                            <div style={{ flex: 1 }}>
                              <Text strong style={{ fontSize: 14 }}>{rec.title}</Text>
                              <div style={{ marginTop: 6 }}>
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                  <UserOutlined /> {rec.author?.name || rec.author || 'Unknown Author'}
                                </Text>
                              </div>
                              <div style={{ marginTop: 8 }}>
                                <Button type="primary" size="small" onClick={() => {
                                  const recId = rec.id || rec.article_id;
                                  console.log('Navigating to modal recommendation:', { rec, recId });
                                  if (recId) {
                                    navigate(`/articles/${recId}`);
                                  } else {
                                    console.error('No ID found for modal recommendation:', rec);
                                  }
                                }}>
                                  Read
                                </Button>
                              </div>
                            </div>
                          </div>
                        </Card>
                      ))
                    ) : (
                      <div style={{ textAlign: 'center', padding: 24 }}>No additional recommendations</div>
                    )}
                  </div>
                </Modal>

                <Card 
                  title={
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <UserOutlined style={{ color: '#1890ff' }} />
                      <span>Popular Authors</span>
                    </div>
                  }
                  style={{ 
                    borderRadius: 16,
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                    border: 'none',
                    marginTop: 16
                  }}
                >
                  {recommendedAuthors.length > 0 ? (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                      {recommendedAuthors.map(a => (
                        <Tag
                          key={a.id}
                          color="blue"
                          style={{ cursor: 'pointer', padding: '4px 10px', borderRadius: 16 }}
                          onClick={() => navigate(`/profile/${a.id}`)}
                        >
                          <UserOutlined style={{ marginRight: 6 }} />
                          {a.full_name || a.name || 'Unknown Author'}
                        </Tag>
                      ))}
                    </div>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '8px', color: '#999' }}>
                      No popular authors found
                    </div>
                  )}
                </Card>
              </div>
            </Col>
          </Row>
        </div>
      </Content>
    </Layout>
  );
};

export default ArticleDetail;
