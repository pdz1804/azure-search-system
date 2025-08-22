/* eslint-disable */
/* @ts-nocheck */
/* JAF-ignore */
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

// Global map to deduplicate fetches across component remounts (helps with React.StrictMode)
const globalFetchMap = new Map();
const globalFetchPromises = new Map();
// Simple per-page cache for search results: key -> { ts, response }
const globalPageCache = new Map();
const PAGE_CACHE_TTL = 300 * 1000; // ms

const _cache_get = (key) => {
  const entry = globalPageCache.get(key);
  if (!entry) return null;
  const { ts, value } = entry;
  if (Date.now() - ts > PAGE_CACHE_TTL) {
    globalPageCache.delete(key);
    return null;
  }
  return value;
};

const _cache_set = (key, value) => {
  globalPageCache.set(key, { ts: Date.now(), value });
};

const ArticleList = ({ 
  authorId = null, 
  category = null,
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
  onBookmarkChange = null,
  currentPage = null,
  onPageChange = null,
  showTopPager = false,
  loadAll = false
}) => {
  const [articles, setArticles] = useState(externalArticles || []);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 12,
  // default to 5 pages * 12 pageSize
  total: 5 * 12
  });
  const [searchText, setSearchText] = useState('');
  const [lastFetchKey, setLastFetchKey] = useState('');
  const [inFlight, setInFlight] = useState(false);
  const navigate = useNavigate();

  // Determine actual loading state
  const isLoading = externalArticles ? externalLoading : loading;
  
  // Create a unique key for caching
  const getCacheKey = () => {
    return `${authorId || 'all'}_${category || 'all'}_${status}_${sortBy}_${searchText}`;
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
    const q = search || searchQuery || searchText;
    const baseKey = `${authorId || 'all'}_${category || 'all'}_${status}_${sortBy}_${q}`;
    const cacheKey = (loadAll && !q)
      ? `${baseKey}_ALL`
      : `${baseKey}_${page}`;
    
    // Check if there's already a promise for this exact fetch
    if (globalFetchPromises.has(cacheKey)) {
      console.log('Reusing existing promise for', cacheKey);
      try {
        const result = await globalFetchPromises.get(cacheKey);
        return result;
      } catch (error) {
        globalFetchPromises.delete(cacheKey);
        throw error;
      }
    }
    
    // If another instance or previous lifecycle already started this fetch, skip
    if (globalFetchMap.has(cacheKey)) {
      console.log('Global fetch already in progress for', cacheKey);
      return;
    }
    if (lastFetchKey === cacheKey) {
      console.log('Skipping duplicate fetch for same cache key', cacheKey);
      return;
    }
    
    // Create and store the promise
    const fetchPromise = performFetch(cacheKey, page, search);
    globalFetchPromises.set(cacheKey, fetchPromise);
    
    try {
      const result = await fetchPromise;
      return result;
    } finally {
      globalFetchPromises.delete(cacheKey);
    }
  };

  const performFetch = async (cacheKey, page, search) => {
    setLoading(true);
    const pageSize = pagination.pageSize || 12;
    try {
      // Helper to normalize and sort results
      const normalize = (raw) => {
        const data = raw?.data ?? raw;
        const itemsSource = Array.isArray(data)
          ? data
          : Array.isArray(data?.items)
            ? data.items
            : Array.isArray(data?.data)
              ? data.data
              : Array.isArray(raw?.results)
                ? raw.results
                : [];
        const sorted = Array.isArray(itemsSource)
          ? [...itemsSource].sort((a, b) => new Date(b.updated_at || b.created_at || 0) - new Date(a.updated_at || a.created_at || 0))
          : itemsSource;
        return { items: sorted, page: (data?.pagination && data.pagination.page) || data?.page || page };
      };

      // mark in-flight globally to survive remounts
      globalFetchMap.set(cacheKey, true);
      // Load-all mode: fetch all pages up to a safe cap
      if (loadAll && !(search || searchQuery)) {
        const accumulated = [];
        const pageSize = 100;
        let current = 1;
        while (true) {
          let resp;
          if (authorId) {
            resp = await articleApi.getArticlesByAuthor(authorId, current, pageSize);
          } else if (category && category !== 'all') {
            resp = await articleApi.getArticlesByCategory(category, current, pageSize);
          } else {
            resp = await articleApi.getArticles({ page: current, page_size: pageSize, limit: pageSize, sort_by: sortBy });
          }
          if (!resp || !resp.success) break;
          const { items } = normalize(resp);
          accumulated.push(...items);
          if (!Array.isArray(items) || items.length < pageSize) break;
          if (current >= 50) break; // safety cap
          current += 1;
        }
        const sortedAll = [...accumulated].sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
        setArticles(sortedAll);
        setPagination(prev => ({ ...prev, total: accumulated.length, pageSize: 12 }));
        setLastFetchKey(cacheKey);
        globalFetchMap.delete(cacheKey);
      } else {
        // Standard single page or search mode
        let response;
        if (authorId) {
          response = await articleApi.getArticlesByAuthor(authorId, page, pagination.pageSize);
        } else if (category && category !== 'all') {
          response = await articleApi.getArticlesByCategory(category, page, pagination.pageSize);
        } else if ((search || searchQuery)) {
          // Server-side paged search: request page with page_size == pagination.pageSize
          const cacheKeyPage = `${cacheKey}_PAGE_${page}`;
          const cached = _cache_get(cacheKeyPage);
          if (cached) {
            console.log('[CACHE HIT]', cacheKeyPage);
            response = cached;
          } else {
            console.log('[CACHE MISS]', cacheKeyPage);
            response = await articleApi.searchArticles(search || searchQuery || searchText, pageSize, page, Math.max(pageSize, 60));
            // store page in cache
            try { _cache_set(cacheKeyPage, response); console.log('[CACHE SET]', cacheKeyPage); } catch (e) { /* ignore */ }
          }
        } else {
          response = await articleApi.getArticles({ page: page, page_size: pagination.pageSize, limit: pagination.pageSize, sort_by: sortBy });
        }

        if (response.success) {
          const { items } = normalize(response);
          const finalItems = (search || searchQuery)
            ? [...items].sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
            : items;
          setArticles(finalItems);
          
          // Extract pagination info - backend returns "total" as number of pages
          const paginationData = response.pagination || {};
          console.log('API Pagination data:', paginationData);

          // Backend returns "total" as number of pages. If missing, default to 5 pages.
          const totalPages = paginationData.total || 5;
          const respPageSize = paginationData.page_size || pagination.pageSize || pageSize || 12;
          const totalItems = totalPages * respPageSize;

          setPagination(prev => ({
            ...prev,
            current: paginationData.page || page,
            // always report total as totalItems (pages * pageSize)
            total: totalItems,
            pageSize: respPageSize
          }));
          setLastFetchKey(cacheKey);
          globalFetchMap.delete(cacheKey);
        } else {
          message.error(response.error || 'Failed to load articles');
          setArticles([]);
        }
  }
    } catch (error) {
      message.error('Failed to load articles');
      console.error('Error fetching articles:', error);
      setArticles([]);
    } finally {
      setLoading(false);
      globalFetchMap.delete(cacheKey);
      setInFlight(false);
    }
  };

  useEffect(() => {
    if (!externalArticles) {
      const startPage = currentPage || 1;
      // sync local pagination with prop if provided
      setPagination(prev => ({ ...prev, current: startPage }));
      fetchArticles(startPage, searchText);
    }
  }, [authorId, category, externalArticles, currentPage]);

  // Separate effect for search/filter changes
  useEffect(() => {
    if (!externalArticles && (searchQuery || tags.length > 0 || status !== 'published' || sortBy !== 'created_at' || category)) {
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
    // If parent controls pagination (controlled component), update local UI state
    // but don't trigger a fetch here — the parent will pass the new `currentPage`
    // prop which is observed by the effect that calls `fetchArticles`.
    if (onPageChange) {
      setPagination(prev => ({ ...prev, current: page }));
      onPageChange(page);
      return;
    }

    setPagination(prev => ({ ...prev, current: page }));
    // For loadAll mode, data is already in memory; otherwise always fetch server page so caching works
    if (!loadAll) {
      fetchArticles(page, searchText);
    }
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
      icon: React.createElement(ExclamationCircleOutlined),
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
        {/* top pager intentionally disabled; only bottom pager will show */}
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
              {(loadAll ? articles.slice((pagination.current - 1) * pagination.pageSize, pagination.current * pagination.pageSize) : articles).map(article => (
                <Col xs={24} sm={12} lg={6} xl={6} key={article.id}>
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

            {showLoadMore && (
              <div style={{ textAlign: 'center', marginTop: 32 }}>
                {/* If this is a search mode (has query), render a simple explicit pager of 5 pages so numbers are always visible and clickable. */}
                {((searchQuery && searchQuery.length > 0) || searchText) ? (
                  (() => {
                    const respPageSize = pagination.pageSize || 12;
                    const pagesFromBackend = Math.max(1, Math.ceil((pagination.total || (5 * respPageSize)) / respPageSize));
                    const pagesToShow = Math.max(5, pagesFromBackend);
                    const buttons = [];
                    for (let i = 1; i <= pagesToShow; i++) {
                      buttons.push(
                        <button
                          key={i}
                          onClick={() => handlePageChange(i)}
                          style={{
                            margin: '0 6px',
                            padding: '6px 10px',
                            borderRadius: 6,
                            border: i === pagination.current ? '2px solid #5b8cff' : '1px solid #ddd',
                            background: i === pagination.current ? '#f0f5ff' : '#fff',
                            cursor: 'pointer'
                          }}
                        >
                          {i}
                        </button>
                      );
                    }
                    return (
                      <div style={{ display: 'inline-flex', alignItems: 'center' }}>
                        <button
                          onClick={() => handlePageChange(Math.max(1, pagination.current - 1))}
                          style={{ marginRight: 8, padding: '6px 10px', borderRadius: 6 }}
                        >
                          &lt;
                        </button>
                        {buttons}
                        <button
                          onClick={() => handlePageChange(Math.min(pagesToShow, pagination.current + 1))}
                          style={{ marginLeft: 8, padding: '6px 10px', borderRadius: 6 }}
                        >
                          &gt;
                        </button>
                      </div>
                    );
                  })()
                ) : (
                  <Pagination
                    current={pagination.current}
                    pageSize={pagination.pageSize}
                    total={pagination.total}
                    onChange={handlePageChange}
                    showSizeChanger={false}
                    showQuickJumper
                    showTotal={(total, range) => `${range[0]}-${range[1]} of ${total} articles`}
                  />
                )}
              </div>
            )}
          </>
        )}
      </Spin>
    </div>
  );
};

export default ArticleList;
