import React, { useState, useEffect } from 'react';
import { message } from 'antd';
import { HeartIcon, BookmarkIcon } from '@heroicons/react/24/outline';
import { HeartIcon as HeartSolid } from '@heroicons/react/24/solid';
import ArticleList from '../components/ArticleList';
import { userApi } from '../api/userApi';
import { articleApi } from '../api/articleApi';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';

/**
 * Bookmarks Page - Displays user's bookmarked articles
 * Uses modern Tailwind styling with proper API integration
 */
const Bookmarks = () => {
  const { user, isAuthenticated } = useAuth();
  const [bookmarkedArticles, setBookmarkedArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isAuthenticated()) {
      fetchBookmarkedArticles();
    } else {
      setLoading(false);
    }
  }, [user]);

  const fetchBookmarkedArticles = async () => {
    try {
      setLoading(true);
      console.log('Fetching bookmarked articles for user:', user);
      
      // Use the dedicated bookmarks API endpoint
      const response = await userApi.getBookmarkedArticles();
      console.log('Bookmarks API response:', response);
      
      if (response.success && response.data) {
        setBookmarkedArticles(response.data);
      } else {
        console.warn('Failed to fetch bookmarks:', response.error);
        setBookmarkedArticles([]);
      }
      
    } catch (error) {
      console.error('Error fetching bookmarked articles:', error);
      message.error('Failed to load bookmarks');
      setBookmarkedArticles([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveBookmark = (articleId) => {
    setBookmarkedArticles(prev => prev.filter(article => article.id !== articleId));
  };

  if (!loading && bookmarkedArticles.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-6 py-12">
          <motion.div 
            className="text-center mb-12"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="flex items-center justify-center mb-6">
              <HeartSolid className="w-8 h-8 text-pink-500 mr-3" />
              <h1 className="text-4xl font-bold text-gray-900">Saved Articles</h1>
            </div>
            <p className="text-xl text-gray-600">Your personal collection of bookmarked content</p>
          </motion.div>

          <motion.div 
            className="bg-white rounded-2xl shadow-lg border border-gray-100 p-12 text-center"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <div className="w-24 h-24 bg-gradient-to-br from-pink-100 to-red-100 rounded-full flex items-center justify-center mx-auto mb-8">
              <BookmarkIcon className="w-12 h-12 text-pink-500" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">No saved articles yet</h2>
            <p className="text-gray-600 text-lg mb-8 max-w-md mx-auto">
              Start building your reading collection by bookmarking articles you want to read later
            </p>
            <div className="bg-gray-50 rounded-xl p-6 max-w-sm mx-auto">
              <div className="flex items-center justify-center mb-3">
                <HeartIcon className="w-5 h-5 text-gray-400 mr-2" />
                <span className="text-sm text-gray-600">Click the heart icon on any article</span>
              </div>
              <p className="text-xs text-gray-500">Bookmarked articles will appear here for easy access</p>
            </div>
          </motion.div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-6 py-12">
        <motion.div 
          className="text-center mb-12"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="flex items-center justify-center mb-6">
            <HeartSolid className="w-8 h-8 text-pink-500 mr-3" />
            <h1 className="text-4xl font-bold text-gray-900">
              Saved Articles 
              <span className="text-2xl text-gray-500 font-normal ml-2">({bookmarkedArticles.length})</span>
            </h1>
          </div>
          <p className="text-xl text-gray-600">Your personal collection of bookmarked content</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <ArticleList 
            articles={bookmarkedArticles}
            loading={loading}
            showLoadMore={false}
            onBookmarkChange={handleRemoveBookmark}
          />
        </motion.div>
      </div>
      
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 flex items-center space-x-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            <span className="text-gray-700 font-medium">Loading your saved articles...</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default Bookmarks;
