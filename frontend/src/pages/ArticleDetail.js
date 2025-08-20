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
  Modal
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
  ExclamationCircleOutlined
} from '@ant-design/icons';
import parse from 'html-react-parser';
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

  useEffect(() => {
    if (id) {
      fetchArticle();
      if (isAuthenticated()) {
        incrementView();
      }
    }
  }, [id]);

  const fetchArticle = async () => {
    try {
      const response = await articleApi.getArticle(id);
      console.log('Article API Response:', response);
      
      if (response.success) {
        const data = response.data;
        console.log('Article Data:', data);
        setArticle(data);
        
        // Kiểm tra follow status nếu user đăng nhập
        if (isAuthenticated() && data.author_id !== user?.id) {
          checkFollowStatus(data.author_id);
        }
      } else {
        message.error(response.error || 'Không thể tải bài viết');
        navigate('/');
      }
    } catch (error) {
      console.error('Error fetching article:', error);
      message.error('Không thể tải bài viết');
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const incrementView = async () => {
    try {
      await articleApi.viewArticle(id);
    } catch (error) {
      // Silent fail
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
      message.warning('Vui lòng đăng nhập để thích bài viết');
      return;
    }
    
    setActionLoading(true);
    try {
      await articleApi.likeArticle(id);
      message.success('Đã thích bài viết');
      fetchArticle();
    } catch (error) {
      message.error('Không thể thích bài viết');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDislike = async () => {
    if (!isAuthenticated()) {
      message.warning('Vui lòng đăng nhập để đánh giá bài viết');
      return;
    }
    
    setActionLoading(true);
    try {
      await articleApi.dislikeArticle(id);
      message.success('Đã không thích bài viết');
      fetchArticle();
    } catch (error) {
      message.error('Không thể đánh giá bài viết');
    } finally {
      setActionLoading(false);
    }
  };

  const handleFollow = async () => {
    if (!isAuthenticated()) {
      message.warning('Vui lòng đăng nhập để theo dõi tác giả');
      return;
    }
    
    setActionLoading(true);
    try {
      if (isFollowing) {
        await userApi.unfollowUser(article.author_id);
        message.success('Đã bỏ theo dõi');
        setIsFollowing(false);
      } else {
        await userApi.followUser(article.author_id);
        message.success('Đã theo dõi');
        setIsFollowing(true);
      }
    } catch (error) {
      message.error('Không thể thực hiện thao tác');
    } finally {
      setActionLoading(false);
    }
  };

  const handleEdit = () => {
    navigate(`/articles/${id}/edit`);
  };

  const handleDelete = () => {
    confirm({
      title: 'Bạn có chắc chắn muốn xóa bài viết này?',
      icon: <ExclamationCircleOutlined />,
      content: 'Bài viết sẽ bị xóa vĩnh viễn.',
      okText: 'Xóa',
      okType: 'danger',
      cancelText: 'Hủy',
      async onOk() {
        try {
          await articleApi.deleteArticle(id);
          message.success('Đã xóa bài viết thành công');
          navigate('/');
        } catch (error) {
          message.error('Không thể xóa bài viết');
        }
      },
    });
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!article) {
    console.log('Article is null/undefined, loading state:', loading);
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Title level={3}>Không tìm thấy bài viết</Title>
      </div>
    );
  }

  console.log('Rendering article:', article);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          <Button 
            icon={<ArrowLeftOutlined />} 
            onClick={() => navigate(-1)}
            style={{ marginBottom: 24 }}
          >
            Quay lại
          </Button>

          <Card>
            {article.image && (
              <img
                src={article.image}
                alt={article.title}
                style={{ width: '100%', height: 300, objectFit: 'cover', marginBottom: 24 }}
              />
            )}

            <Title level={1}>{article.title}</Title>
            
            <div style={{ marginBottom: 24 }}>
              <Space size="large">
                <Space>
                  <Avatar src={article.author?.avatar_url}>
                    {(article.author_name || article.author?.full_name || 'U')?.[0]}
                  </Avatar>
                  <div>
                    <Text strong>{article.author_name || article.author?.full_name || 'Unknown Author'}</Text>
                    <br />
                    <Text type="secondary">{formatDate(article.created_at)}</Text>
                  </div>
                </Space>
                
                {isAuthenticated() && article.author_id !== user?.id && (
                  <Button
                    type={isFollowing ? "default" : "primary"}
                    icon={isFollowing ? <UserDeleteOutlined /> : <UserAddOutlined />}
                    onClick={handleFollow}
                    loading={actionLoading}
                  >
                    {isFollowing ? 'Bỏ theo dõi' : 'Theo dõi'}
                  </Button>
                )}
              </Space>
            </div>

            <div style={{ marginBottom: 24 }}>
              {article.tags && Array.isArray(article.tags) && article.tags.map(tag => (
                <Tag key={tag} color="blue">{tag}</Tag>
              ))}
            </div>

            <Paragraph style={{ fontSize: 16, fontStyle: 'italic' }}>
              {article.abstract}
            </Paragraph>

            <Divider />

            <div style={{ lineHeight: 1.8, fontSize: 16 }}>
              {(() => {
                console.log('Article content type:', typeof article.content, 'Content:', article.content);
                if (article.content && typeof article.content === 'string') {
                  return parse(article.content);
                } else {
                  return <Text type="secondary">Nội dung không có sẵn (content: {JSON.stringify(article.content)})</Text>;
                }
              })()}
            </div>

            <Divider />

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Space size="large">
                <Text type="secondary">
                  <EyeOutlined /> {formatNumber(article.views || 0)} lượt xem
                </Text>
                <Text type="secondary">
                  <LikeOutlined /> {formatNumber(article.likes || 0)} thích
                </Text>
                <Text type="secondary">
                  <DislikeOutlined /> {formatNumber(article.dislikes || 0)} không thích
                </Text>
              </Space>

              <Space>
                {isAuthenticated() && (
                  <>
                    <Button
                      icon={<LikeOutlined />}
                      onClick={handleLike}
                      loading={actionLoading}
                    >
                      Thích
                    </Button>
                    <Button
                      icon={<DislikeOutlined />}
                      onClick={handleDislike}
                      loading={actionLoading}
                    >
                      Không thích
                    </Button>
                  </>
                )}

                {canEditArticle(article) && (
                  <>
                    <Button
                      type="primary"
                      icon={<EditOutlined />}
                      onClick={handleEdit}
                    >
                      Sửa
                    </Button>
                    <Button
                      danger
                      icon={<DeleteOutlined />}
                      onClick={handleDelete}
                    >
                      Xóa
                    </Button>
                  </>
                )}
              </Space>
            </div>
          </Card>
        </div>
      </Content>
    </Layout>
  );
};

export default ArticleDetail;
