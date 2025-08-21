/* eslint-disable */
/* @ts-nocheck */
/* JAF-ignore */
import React, { useState, useEffect } from 'react';
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
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { articleApi } from '../api/articleApi';
import { userApi } from '../api/userApi';
import { useAuth } from '../context/AuthContext';
import { formatDate, formatNumber } from '../utils/helpers';

const { Content } = Layout;
const { Title, Text, Paragraph } = Typography;
const { confirm } = Modal;

const ArticleDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, isAuthenticated, canEditArticle } = useAuth();
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isFollowing, setIsFollowing] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [reactionType, setReactionType] = useState('none');
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [recommendations, setRecommendations] = useState([]);
  const [recommendationsLoading, setRecommendationsLoading] = useState(false);
  const [recommendedAuthors, setRecommendedAuthors] = useState([]);

  useEffect(() => {
    if (id) {
      fetchArticle();
      fetchRecommendations();
      if (isAuthenticated()) {
        loadUserReactionStatus();
      }
    }
  }, [id]); // Remove user from dependency array to prevent re-fetching

  const fetchArticle = async () => {
    try {
      setLoading(true);
      console.log('Fetching article with ID:', id);
      
      // Fetch article data
      const response = await articleApi.getArticle(id);
      console.log('Article API Response:', response);
      
      if (response.success) {
        const data = response.data;
        console.log('Article Data:', data);
        setArticle(data);
        
        // Check follow status if user is logged in and not the author
        if (isAuthenticated() && data.author_id !== user?.id) {
          checkFollowStatus(data.author_id);
        }
      } else {
        console.error('Article API returned error:', response.error);
        message.error(response.error || 'Cannot load article');
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

  const fetchRecommendations = async () => {
    try {
      setRecommendationsLoading(true);
      // Use article content to search similar articles
      if (article?.content) {
        const contentQuery = (article.content || '').slice(0, 4000);
        const resp = await articleApi.searchArticles(contentQuery, 5, 1, 5);
        const items = resp.results || resp.data || [];
        const filtered = items.filter(rec => rec.id !== id).slice(0, 5);
        setRecommendations(filtered);
      } else {
        const response = await articleApi.getPopularArticles(10);
        if (response.success && response.data) {
          const filtered = response.data.filter(rec => rec.id !== id).slice(0, 5);
          setRecommendations(filtered);
        }
      }
    } catch (error) {
      console.error('Error fetching recommendations:', error);
    } finally {
      setRecommendationsLoading(false);
    }
  };

  useEffect(() => {
    // Load recommended authors: top 5 from the authors that this article's author follows
    const loadRecommendedAuthors = async () => {
      try {
        if (!article?.author_id) return;
        // We don't have an API to list followings; approximate by loading users and picking top followers
        const usersResp = await userApi.getAllUsers(1, 100);
        if (usersResp.success) {
          const items = usersResp.data?.items || usersResp.data || [];
          const top = [...items].sort((a, b) => (b.followers || 0) - (a.followers || 0)).slice(0, 5);
          setRecommendedAuthors(top);
        }
      } catch (e) {
        // silent
      }
    };
    loadRecommendedAuthors();
  }, [article?.author_id]);

  const loadUserReactionStatus = async () => {
    try {
      const res = await userApi.checkArticleReactionStatus(id);
      if (res.success) {
        const { reaction_type, is_bookmarked } = res.data;
        setReactionType(reaction_type || 'none');
        setIsBookmarked(is_bookmarked || false);
        console.log('Loaded user reaction status:', { reaction_type, is_bookmarked });
      }
    } catch (error) {
      console.error('Error loading user reaction status:', error);
      // Set default values on error
      setReactionType('none');
      setIsBookmarked(false);
    }
  };

  const checkFollowStatus = async (authorId) => {
    try {
      const response = await userApi.checkFollowStatus(authorId);
      setIsFollowing(response.is_following);
    } catch (error) {
      // Silent fail
    }
  };

  const handleLike = async () => {
    if (!isAuthenticated()) {
      message.warning('Please login to like articles');
      return;
    }
    
    try {
    setActionLoading(true);
      let response;
      
      if (reactionType === 'like') {
        response = await userApi.unlikeArticle(id);
        if (response.success) {
          setReactionType('none');
          setArticle(prev => ({ ...prev, likes: Math.max(0, (prev?.likes || 0) - 1) }));
          message.success('Article unliked');
        }
      } else {
        // If currently disliked, remove dislike first
        if (reactionType === 'dislike') {
          await userApi.undislikeArticle(id);
          setArticle(prev => ({ ...prev, dislikes: Math.max(0, (prev?.dislikes || 0) - 1) }));
        }
        
        response = await userApi.likeArticle(id);
        if (response.success) {
          setReactionType('like');
          setArticle(prev => ({ ...prev, likes: (prev?.likes || 0) + 1 }));
          message.success('Article liked');
        }
      }
    } catch (error) {
      console.error('Error handling like:', error);
      message.error('Failed to update like status');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDislike = async () => {
    if (!isAuthenticated()) {
      message.warning('Please login to dislike articles');
      return;
    }
    
    try {
      setActionLoading(true);
      let response;
      
      if (reactionType === 'dislike') {
        response = await userApi.undislikeArticle(id);
        if (response.success) {
          setReactionType('none');
          setArticle(prev => ({ ...prev, dislikes: Math.max(0, (prev?.dislikes || 0) - 1) }));
          message.success('Article undisliked');
        }
      } else {
        // If currently liked, remove like first
        if (reactionType === 'like') {
          await userApi.unlikeArticle(id);
          setArticle(prev => ({ ...prev, likes: Math.max(0, (prev?.likes || 0) - 1) }));
        }
        
        response = await userApi.dislikeArticle(id);
        if (response.success) {
          setReactionType('dislike');
          setArticle(prev => ({ ...prev, dislikes: (prev?.dislikes || 0) + 1 }));
          message.success('Article disliked');
        }
      }
    } catch (error) {
      console.error('Error handling dislike:', error);
      message.error('Failed to update dislike status');
    } finally {
      setActionLoading(false);
    }
  };

  const toggleBookmark = async () => {
    if (!isAuthenticated()) {
      message.warning('Please login to bookmark articles');
      return;
    }
    setActionLoading(true);
    try {
      if (isBookmarked) {
        const res = await userApi.unbookmarkArticle(id);
        if (res.success) setIsBookmarked(false);
      } else {
        const res = await userApi.bookmarkArticle(id);
        if (res.success) setIsBookmarked(true);
      }
    } catch {
      message.error('Failed to update bookmark status');
    } finally {
      setActionLoading(false);
    }
  };

  const handleFollow = async () => {
    if (!isAuthenticated()) {
      message.warning('Please login to follow authors');
      return;
    }
    
    setActionLoading(true);
    try {
      if (isFollowing) {
        await userApi.unfollowUser(article.author_id);
        message.success('Unfollowed');
        setIsFollowing(false);
      } else {
        await userApi.followUser(article.author_id);
        message.success('Followed');
        setIsFollowing(true);
      }
    } catch (error) {
      message.error('Failed to perform action');
    } finally {
      setActionLoading(false);
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

  console.log('Rendering article:', article);

  const calculateReadingTime = (content) => {
    if (!content) return 0;
    const words = content.split(/\s+/).length;
    const readingSpeed = 200; // Average words per minute
    return Math.ceil(words / readingSpeed);
  };

  const likesCount = article.likes || 0;
  const dislikesCount = article.dislikes || 0;

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
                      src={article.author_avatar_url}
                      style={{ cursor: 'pointer' }}
                      onClick={() => navigate(`/profile/${article.author_id}`)}
                    >
                      {article.author_name?.[0] || 'A'}
                    </Avatar>
                    
                    <div style={{ flex: 1 }}>
                      <Text 
                        strong 
                        style={{ 
                          fontSize: 16, 
                          cursor: 'pointer',
                          color: '#1890ff'
                        }}
                        onClick={() => navigate(`/profile/${article.author_id}`)}
                      >
                        {article.author_name}
                      </Text>
                      <br />
                      <Space size={16}>
                        <Text type="secondary" style={{ fontSize: 14 }}>
                          <ClockCircleOutlined style={{ marginRight: 4 }} />
                          {formatDate(article.created_at)}
                        </Text>
                        <Text type="secondary" style={{ fontSize: 14 }}>
                          <EyeOutlined style={{ marginRight: 4 }} />
                          {calculateReadingTime(article.content)} min read
                        </Text>
                        {article.views > 0 && (
                          <Text type="secondary" style={{ fontSize: 14 }}>
                            <EyeOutlined style={{ marginRight: 4 }} />
                            {formatNumber(article.views)} views
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
                        fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMIAAADDCAYAAADQvc6UAAABRWlDQ1BJQ0MgUHJvZmlsZQAAKJFjYGASSSwoyGFhYGDIzSspCnJ3UoiIjFJgf8LAwSDCIMogwMCcmFxc4BgQ4ANUwgCjUcG3awyMIPqyLsis7PPOq3QdDFcvjV3jOD1boQVTPQrgSkktTgbSf4A4LbmgqISBgTEFyFYuLykAsTuAbJEioKOA7DkgdjqEvQHEToKwj4DVhAQ5A9k3gGyB5IxEoBmML4BsnSQk8XQkNtReEOBxcfXxUQg1Mjc0dyHgXNJBSWpFCYh2zi+oLMpMzyhRcASGUqqCZ16yno6CkYGRAQMDKMwhqj/fAIcloxgHQqxAjIHBEugw5sUIsSQpBobtQPdLciLEVJYzMPBHMDBsayhILEqEO4DxG0txmrERhM29nYGBddr//5/DGRjYNRkY/l7////39v///y4Dmn+LgeHANwDrkl1AuO+pmgAAADhlWElmTU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAAqACAAQAAAABAAAAwqADAAQAAAABAAAAwwAAAAD9b/HnAAAHlklEQVR4Ae3dP3Ik1RnG4W+FgYxN"
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
                    loading={actionLoading}
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
                    loading={actionLoading}
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
                    loading={actionLoading}
                    style={{ 
                      borderRadius: 20,
                      height: 40,
                      paddingLeft: 20,
                      paddingRight: 20
                    }}
                  >
                    {isBookmarked ? 'Bookmarked' : 'Bookmark'}
                  </Button>
                
                {isAuthenticated() && article.author_id !== user?.id && (
                  <Button
                    type={isFollowing ? "default" : "primary"}
                    icon={isFollowing ? <UserDeleteOutlined /> : <UserAddOutlined />}
                    onClick={handleFollow}
                    loading={actionLoading}
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
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <BookOutlined style={{ color: '#1890ff' }} />
                      <span>Recommended Articles</span>
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
                  ) : recommendations.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                      {recommendations.map((rec) => (
                        <Card 
                          key={rec.id} 
                          size="small" 
                          hoverable
                          style={{ cursor: 'pointer' }}
                          onClick={() => navigate(`/articles/${rec.id}`)}
                          bodyStyle={{ padding: 12 }}
                        >
                          <div style={{ display: 'flex', gap: 12 }}>
                            {rec.image && (
                              <Image
                                src={rec.image}
                                alt={rec.title}
                                width={60}
                                height={60}
                                style={{ objectFit: 'cover', borderRadius: 4 }}
                                fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMIAAADDCAYAAADQvc6UAAABRWlDQ1BJQ0MgUHJvZmlsZQAAKJFjYGASSSwoyGFhYGDIzSspCnJ3UoiIjFJgf8LAwSDCIMogwMCcmFxc4BgQ4ANUwgCjUcG3awyMIPqyLsis7PPOq3QdDFcvjV3jOD1boQVTPQrgSkktTgbSf4A4LbmgqISBgTEFyFYuLykAsTuAbJEioKOA7DkgdjqEvQHEToKwj4DVhAQ5A9k3gGyB5IxEoBmML4BsnSQk8XQkNtReEOBxcfXxUQg1Mjc0dyHgXNJBSWpFCYh2zi+oLMpMzyhRcASGUqqCZ16yno6CkYGRAQMDKMwhqj/fAIcloxgHQqxAjIHBEugw5sUIsSQpBobtQPdLciLEVJYzMPBHMDBsayhILEqEO4DxG0txmrERhM29nYGBddr//5/DGRjYNRkY/l7////39v///y4Dmn+LgeHANwDrkl1AuO+pmgAAADhlWElmTU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAAqACAAQAAAABAAAAwqADAAQAAAABAAAAwwAAAAD9b/HnAAAHlklEQVR4Ae3dP3Ik1RnG4W+FgYxN"
                              />
                            )}
                            <div style={{ flex: 1, minWidth: 0 }}>
                              <Text 
                                strong 
                                style={{ 
                                  fontSize: 14, 
                                  lineHeight: 1.4,
                                  display: '-webkit-box',
                                  WebkitLineClamp: 2,
                                  WebkitBoxOrient: 'vertical',
                                  overflow: 'hidden'
                                }}
                              >
                                {rec.title}
                              </Text>
                              <div style={{ marginTop: 4 }}>
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                  <UserOutlined style={{ marginRight: 4 }} />
                                  {rec.author_name}
                                </Text>
                              </div>
                              <div style={{ marginTop: 2 }}>
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                  <ClockCircleOutlined style={{ marginRight: 4 }} />
                                  {formatDate(rec.created_at)}
                                </Text>
                              </div>
                            </div>
            </div>
          </Card>
                      ))}
                    </div>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
                      <BookOutlined style={{ fontSize: 24, marginBottom: 8 }} />
                      <div>No recommendations yet</div>
                    </div>
                  )}
                </Card>

                <Card 
                  title={
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <UserOutlined style={{ color: '#1890ff' }} />
                      <span>Recommended Authors</span>
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
                          {a.full_name}
                        </Tag>
                      ))}
                    </div>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '8px', color: '#999' }}>
                      No recommended authors
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
