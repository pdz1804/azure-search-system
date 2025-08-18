import React from 'react';
import { Card, Tag, Avatar, Button, Space, Typography } from 'antd';
import { EyeOutlined, LikeOutlined, DislikeOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { formatDate, formatNumber, truncateText } from '../utils/helpers';

const { Meta } = Card;
const { Text } = Typography;

const ArticleCard = ({ article, onEdit, onDelete, onLike, onDislike }) => {
  const navigate = useNavigate();
  const { user, canEditArticle } = useAuth();
  
  const handleClick = () => {
    navigate(`/articles/${article.id}`);
  };

  const handleAuthorClick = (e) => {
    e.stopPropagation();
    navigate(`/profile/${article.author_id}`);
  };

  const handleEdit = (e) => {
    e.stopPropagation();
    onEdit && onEdit(article);
  };

  const handleDelete = (e) => {
    e.stopPropagation();
    onDelete && onDelete(article);
  };

  const handleLike = (e) => {
    e.stopPropagation();
    onLike && onLike(article.id);
  };

  const handleDislike = (e) => {
    e.stopPropagation();
    onDislike && onDislike(article.id);
  };

  const actions = [
    <Space key="stats">
      <Text type="secondary">
        <EyeOutlined /> {formatNumber(article.views)}
      </Text>
      <Text type="secondary">
        <LikeOutlined /> {formatNumber(article.likes)}
      </Text>
      <Text type="secondary">
        <DislikeOutlined /> {formatNumber(article.dislikes)}
      </Text>
    </Space>
  ];

  if (user) {
    const interactionActions = [
      <Button
        key="like"
        type="text"
        icon={<LikeOutlined />}
        onClick={handleLike}
        size="small"
      >
        Thích
      </Button>,
      <Button
        key="dislike"
        type="text"
        icon={<DislikeOutlined />}
        onClick={handleDislike}
        size="small"
      >
        Không thích
      </Button>
    ];

    if (canEditArticle(article)) {
      interactionActions.push(
        <Button
          key="edit"
          type="text"
          icon={<EditOutlined />}
          onClick={handleEdit}
          size="small"
        >
          Sửa
        </Button>,
        <Button
          key="delete"
          type="text"
          danger
          icon={<DeleteOutlined />}
          onClick={handleDelete}
          size="small"
        >
          Xóa
        </Button>
      );
    }

    actions.push(...interactionActions);
  }

  return (
    <Card
      hoverable
      style={{ marginBottom: 16 }}
      cover={
        article.image && (
          <img
            alt={article.title}
            src={article.image}
            style={{ height: 200, objectFit: 'cover' }}
          />
        )
      }
      actions={actions}
      onClick={handleClick}
    >
      <Meta
        avatar={
          <Avatar 
            src={article.author?.avatar_url || article.avatar_url} 
            onClick={handleAuthorClick}
            style={{ cursor: 'pointer' }}
          >
            {(article.author_name || article.author?.full_name)?.[0]}
          </Avatar>
        }
        title={article.title}
        description={
          <div>
            <Text type="secondary" onClick={handleAuthorClick} style={{ cursor: 'pointer' }}>
              {article.author_name || article.author?.full_name || 'Unknown Author'}
            </Text>
            <br />
            <Text type="secondary">{formatDate(article.created_at)}</Text>
            <br />
            <div style={{ margin: '8px 0' }}>
              {article.tags?.map(tag => (
                <Tag key={tag} color="blue">{tag}</Tag>
              ))}
            </div>
            <Text>{truncateText(article.abstract || article.content, 150)}</Text>
          </div>
        }
      />
    </Card>
  );
};

export default ArticleCard;
