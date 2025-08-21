import React, { useState, useEffect } from 'react';
import { Row, Col, Pagination, Input, Select, Spin, Empty, message, Modal } from 'antd';
import { ExclamationCircleOutlined } from '@ant-design/icons';
import ArticleCard from './ArticleCard';
import { articleApi } from '../api/articleApi';
import { userApi } from '../api/userApi';
import { useNavigate } from 'react-router-dom';

const { Search } = Input;
const { Option } = Select;
const { confirm } = Modal;

const ArticleList = ({ 
  authorId = null, 
  title = "Article List",
  articles: externalArticles = null,
  loading: externalLoading = false,
  showLoadMore = true,
  showFilters = true,
  showAuthor = true,
  searchQuery = '',
  tags = [],
  status = 'published',
  sortBy = 'created_at',
  onRefresh = null,
  onBookmarkChange = null
}) => {
  const [articles, setArticles] = useState(externalArticles || []);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 12,
    total: 0
  });
  const [searchText, setSearchText] = useState('');
  const [lastFetchKey, setLastFetchKey] = useState('');
  const navigate = useNavigate();

  // Determine actual loading state
  const isLoading = externalArticles ? externalLoading : loading;
  
  // Create a unique key for caching
  const getCacheKey = () => {
    return `${authorId || 'all'}_${status}_${sortBy}_${searchText}`;
  };
  
  // Debug log
  console.log('ArticleList Debug:', { 
    externalArticles: !!externalArticles, 
    externalLoading, 
    loading, 
    isLoading, 
    articlesCount: articles.length,
    cacheKey: getCacheKey()
  });

  const fetchArticles = async (page = 1, search = '') => {
    if (externalArticles) return; // Don't fetch if articles are provided externally
    
    const cacheKey = getCacheKey();
    if (lastFetchKey === cacheKey && page === 1) {
      console.log('Skipping duplicate fetch for same cache key');
      return;
    }
    
    setLoading(true);
    try {
      let response;
      const params = {
        page,
        page_size: pagination.pageSize,
        q: search || searchQuery,
        status: status !== 'all' ? status : undefined,
        tags: tags.length > 0 ? tags.join(',') : undefined,
        sort_by: sortBy
      };

      if (authorId) {
        response = await articleApi.getArticlesByAuthor(authorId, page, pagination.pageSize);
      } else {
        response = await articleApi.getArticles(params);
      }
      
      // Handle API response structure
      if (response.success) {
        const data = response.data;
        setArticles(data.items || data.data || data || []);
        setPagination(prev => ({
          ...prev,
          current: data.page || data.currentPage || page,
          total: data.total || data.totalItems || data.total_items || 0
        }));
        setLastFetchKey(cacheKey);
      } else {
        message.error(response.error || 'Failed to load articles');
        setArticles([]);
      }
    } catch (error) {
      message.error('Failed to load articles');
      console.error('Error fetching articles:', error);
      setArticles([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!externalArticles) {
      fetchArticles(1, searchText);
    }
  }, [authorId, externalArticles]); // Chỉ re-fetch khi authorId hoặc externalArticles thay đổi

  // Separate effect for search/filter changes
  useEffect(() => {
    if (!externalArticles && (searchQuery || tags.length > 0 || status !== 'published' || sortBy !== 'created_at')) {
      fetchArticles(1, searchQuery);
    }
  }, [searchQuery, tags, status, sortBy]);

  useEffect(() => {
    if (externalArticles) {
      setArticles(externalArticles);
      setLoading(false);
    }
  }, [externalArticles]);

  const handlePageChange = (page) => {
    fetchArticles(page, searchText);
  };

  const handleSearch = (value) => {
    setSearchText(value);
    fetchArticles(1, value);
  };

  const handleEdit = (article) => {
    navigate(`/write/${article.id}`);
  };

  const handleDelete = (article) => {
    confirm({
      title: 'Are you sure you want to delete this article?',
      icon: <ExclamationCircleOutlined />,
      content: `Article "${article.title}" will be permanently deleted.`,
      okText: 'Delete',
      okType: 'danger',
      cancelText: 'Cancel',
      async onOk() {
        try {
          await articleApi.deleteArticle(article.id);
          message.success('Article deleted successfully');
          fetchArticles(pagination.current, searchText);
        } catch (error) {
          message.error('Failed to delete article');
        }
      },
    });
  };

  const handleLike = async (articleId) => {
    try {
      await userApi.likeArticle(articleId);
      message.success('Article liked');
      fetchArticles(pagination.current, searchText);
    } catch (error) {
      message.error('Failed to like article');
    }
  };

  const handleDislike = async (articleId) => {
    try {
      await userApi.dislikeArticle(articleId);
      message.success('Article disliked');
      fetchArticles(pagination.current, searchText);
    } catch (error) {
      message.error('Failed to dislike article');
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ 
          color: '#1a1a1a', 
          fontSize: 24, 
          fontWeight: 600,
          marginBottom: 16
        }}>
          {title}
        </h2>
        {showFilters && !authorId && (
          <Search
            placeholder="Search articles..."
            allowClear
            enterButton="Search"
            size="large"
            onSearch={handleSearch}
            style={{ 
              maxWidth: 400,
              borderRadius: 20
            }}
          />
        )}
      </div>

      <Spin spinning={isLoading}>
        {articles.length === 0 && !isLoading ? (
          <Empty 
            description="No articles found" 
            style={{ 
              padding: '60px 0',
              color: '#666'
            }}
          />
        ) : (
          <>
            <Row gutter={[16, 16]}>
              {articles.map(article => (
                <Col xs={24} sm={12} lg={8} xl={6} key={article.id}>
                  <ArticleCard
                    article={article}
                    onEdit={handleEdit}
                    onDelete={handleDelete}
                    onLike={handleLike}
                    onDislike={handleDislike}
                  />
                </Col>
              ))}
            </Row>

            {showLoadMore && pagination.total > pagination.pageSize && (
              <div style={{ textAlign: 'center', marginTop: 32 }}>
                <Pagination
                  current={pagination.current}
                  pageSize={pagination.pageSize}
                  total={pagination.total}
                  onChange={handlePageChange}
                  showSizeChanger={false}
                  showQuickJumper
                  showTotal={(total, range) =>
                    `${range[0]}-${range[1]} of ${total} articles`
                  }
                />
              </div>
            )}
          </>
        )}
      </Spin>
    </div>
  );
};

export default ArticleList;
