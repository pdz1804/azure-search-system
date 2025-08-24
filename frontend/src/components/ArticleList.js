/* eslint-disable */
/* @ts-nocheck */
/* JAF-ignore */
import React, { useState, useEffect } from 'react';
import { ExclamationTriangleIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import ArticleCard from './ArticleCard';
import { articleApi } from '../api/articleApi';
import { userApi } from '../api/userApi';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

// Redis caching is now handled on the backend - no frontend cache needed
// Global map to deduplicate fetches across component remounts (helps with React.StrictMode)
const globalFetchMap = new Map();
const globalFetchPromises = new Map();

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
  
  // Debug log removed to prevent console spam

  const fetchArticles = async (page = 1, search = '') => {
    if (externalArticles) return; // Don't fetch if articles are provided externally
    const q = search || searchQuery || searchText;
    const baseKey = `${authorId || 'all'}_${category || 'all'}_${status}_${sortBy}_${q}`;
    const cacheKey = (loadAll && !q)
      ? `${baseKey}_ALL`
      : `${baseKey}_${page}`;
    
    // Check if there's already a promise for this exact fetch
    if (globalFetchPromises.has(cacheKey)) {
      // Reusing existing promise
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
      // Global fetch already in progress
      return;
    }
    if (lastFetchKey === cacheKey) {
      // Skipping duplicate fetch for same cache key
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
          // Server-side paged search with Redis caching on backend
          response = await articleApi.searchArticles(search || searchQuery || searchText, pageSize, page, Math.max(pageSize, 60));
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
          // API Pagination data received

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

  // Single unified effect to prevent duplicate API calls
  useEffect(() => {
    if (!externalArticles && !inFlight) {
      const pageToFetch = currentPage || 1;
      setPagination(prev => ({ ...prev, current: pageToFetch }));
      fetchArticles(pageToFetch, searchQuery || searchText);
    }
  }, [
    authorId, 
    category, 
    externalArticles, 
    currentPage, 
    searchQuery, 
    JSON.stringify(tags), 
    status, 
    sortBy
  ]);

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
    if (window.confirm(`Are you sure you want to delete "${article.title}"? This action cannot be undone.`)) {
      deleteArticle(article);
    }
  };

  const deleteArticle = async (article) => {
    try {
      await articleApi.deleteArticle(article.id);
      toast.success('Article deleted successfully');
      fetchArticles(pagination.current, searchText);
    } catch (error) {
      toast.error('Failed to delete article');
    }
  };

  const handleLike = async (articleId) => {
    try {
      await userApi.likeArticle(articleId);
      toast.success('Article liked');
      fetchArticles(pagination.current, searchText);
    } catch (error) {
      toast.error('Failed to like article');
    }
  };

  const handleDislike = async (articleId) => {
    try {
      await userApi.dislikeArticle(articleId);
      toast.success('Article disliked');
      fetchArticles(pagination.current, searchText);
    } catch (error) {
      toast.error('Failed to dislike article');
    }
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">
          {title}
        </h2>
        {showFilters && !authorId && (
          <div className="relative max-w-md">
            <input
              type="text"
              placeholder="Search articles..."
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleSearch(e.target.value);
                }
              }}
              className="w-full px-4 py-3 pl-12 pr-4 text-gray-700 bg-white border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent shadow-sm"
            />
            <MagnifyingGlassIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          </div>
        )}
      </div>

      <div className="relative">
        {isLoading && (
          <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
        )}
        
        {articles.length === 0 && !isLoading ? (
          <div className="text-center py-16">
            <div className="w-16 h-16 mx-auto mb-4 text-gray-400">
              <svg fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 0v12h8V4H6z" clipRule="evenodd" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No articles found</h3>
            <p className="text-gray-500">Try adjusting your search criteria or check back later.</p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {(loadAll ? articles.slice((pagination.current - 1) * pagination.pageSize, pagination.current * pagination.pageSize) : articles).map(article => (
                <div key={article.id} className="h-full">
                  <ArticleCard
                    article={article}
                    onEdit={handleEdit}
                    onDelete={handleDelete}
                    onLike={handleLike}
                    onDislike={handleDislike}
                    layout="grid"
                  />
                </div>
              ))}
            </div>

            {showLoadMore && (
              <div className="flex justify-center mt-8">
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
                          className={`mx-1 px-3 py-2 rounded-lg font-medium transition-colors ${
                            i === pagination.current
                              ? 'bg-indigo-600 text-white border-2 border-indigo-600'
                              : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                          }`}
                        >
                          {i}
                        </button>
                      );
                    }
                    return (
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handlePageChange(Math.max(1, pagination.current - 1))}
                          disabled={pagination.current === 1}
                          className="px-3 py-2 rounded-lg border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          ←
                        </button>
                        {buttons}
                        <button
                          onClick={() => handlePageChange(Math.min(pagesToShow, pagination.current + 1))}
                          disabled={pagination.current === pagesToShow}
                          className="px-3 py-2 rounded-lg border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          →
                        </button>
                      </div>
                    );
                  })()
                ) : (
                  <div className="flex items-center justify-center space-x-4">
                    <button
                      onClick={() => handlePageChange(Math.max(1, pagination.current - 1))}
                      disabled={pagination.current === 1}
                      className="px-4 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Previous
                    </button>
                    <span className="text-sm text-gray-700">
                      Page {pagination.current} of {Math.ceil(pagination.total / pagination.pageSize)}
                    </span>
                    <button
                      onClick={() => handlePageChange(pagination.current + 1)}
                      disabled={pagination.current >= Math.ceil(pagination.total / pagination.pageSize)}
                      className="px-4 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default ArticleList;
