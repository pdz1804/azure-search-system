import React, { useState, useEffect } from 'react';
import { Row, Col, Pagination, Input, Select, Spin, Empty, message, Modal } from 'antd';
import { ExclamationCircleOutlined } from '@ant-design/icons';
import ArticleCard from './ArticleCard';
import { articleApi } from '../api/articleApi';
import { useNavigate } from 'react-router-dom';

const { Search } = Input;
const { Option } = Select;
const { confirm } = Modal;

const ArticleList = ({ 
  authorId = null, 
  title = "Danh sách bài viết",
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
  const navigate = useNavigate();

  // Determine actual loading state
  const isLoading = externalArticles ? externalLoading : loading;
  
  // Debug log
  console.log('ArticleList Debug:', { 
    externalArticles: !!externalArticles, 
    externalLoading, 
    loading, 
    isLoading, 
    articlesCount: articles.length 
  });

  const fetchArticles = async (page = 1, search = '') => {
    if (externalArticles) return; // Don't fetch if articles are provided externally
    
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
      
      setArticles(response.items || response.data || []);
      setPagination(prev => ({
        ...prev,
        current: response.page || response.currentPage || page,
        total: response.total || response.totalItems || 0
      }));
    } catch (error) {
      message.error('Không thể tải danh sách bài viết');
      console.error('Error fetching articles:', error);
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
    navigate(`/articles/${article.id}/edit`);
  };

  const handleDelete = (article) => {
    confirm({
      title: 'Bạn có chắc chắn muốn xóa bài viết này?',
      icon: <ExclamationCircleOutlined />,
      content: `Bài viết "${article.title}" sẽ bị xóa vĩnh viễn.`,
      okText: 'Xóa',
      okType: 'danger',
      cancelText: 'Hủy',
      async onOk() {
        try {
          await articleApi.deleteArticle(article.id);
          message.success('Đã xóa bài viết thành công');
          fetchArticles(pagination.current, searchText);
        } catch (error) {
          message.error('Không thể xóa bài viết');
        }
      },
    });
  };

  const handleLike = async (articleId) => {
    try {
      await articleApi.likeArticle(articleId);
      message.success('Đã thích bài viết');
      fetchArticles(pagination.current, searchText);
    } catch (error) {
      message.error('Không thể thích bài viết');
    }
  };

  const handleDislike = async (articleId) => {
    try {
      await articleApi.dislikeArticle(articleId);
      message.success('Đã không thích bài viết');
      fetchArticles(pagination.current, searchText);
    } catch (error) {
      message.error('Không thể đánh giá bài viết');
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h2>{title}</h2>
        {showFilters && !authorId && (
          <Search
            placeholder="Tìm kiếm bài viết..."
            allowClear
            enterButton="Tìm kiếm"
            size="large"
            onSearch={handleSearch}
            style={{ maxWidth: 400 }}
          />
        )}
      </div>

      <Spin spinning={isLoading}>
        {articles.length === 0 && !isLoading ? (
          <Empty description="Không có bài viết nào" />
        ) : articles.length > 0 ? (
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
                    `${range[0]}-${range[1]} của ${total} bài viết`
                  }
                />
              </div>
            )}
          </>
        ) : null}
      </Spin>
    </div>
  );
};

export default ArticleList;
