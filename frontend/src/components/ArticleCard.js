import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { LazyLoadImage } from 'react-lazy-load-image-component';
import { 
  HeartIcon, 
  EyeIcon, 
  ClockIcon, 
  BookmarkIcon,
  UserIcon,
  TagIcon,
  PencilIcon,
  TrashIcon
} from '@heroicons/react/24/outline';
import { 
  HeartIcon as HeartSolidIcon,
  BookmarkIcon as BookmarkSolidIcon
} from '@heroicons/react/24/solid';
import { format, formatDistanceToNow } from 'date-fns';
import toast from 'react-hot-toast';

import { useAuth } from '../context/AuthContext';
import { userApi } from '../api/userApi';
import { formatDate, formatNumber, truncateText } from '../utils/helpers';

const ArticleCard = ({ 
  article, 
  layout = 'grid', // 'grid', 'list', 'featured'
  showAuthor = true,
  showActions = true,
  onEdit, 
  onDelete, 
  onLike, 
  onDislike,
  className = ''
}) => {
  const navigate = useNavigate();
  const { user, canEditArticle } = useAuth();
  const [userReaction, setUserReaction] = useState('none');
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [likesCount, setLikesCount] = useState(article.likes || 0);
  const [reactionLoading, setReactionLoading] = useState(false);
  const [statusLoaded, setStatusLoaded] = useState(false);

  // Load user's reaction status when component mounts
  useEffect(() => {
    if (user && !statusLoaded) {
      loadUserReactionStatus();
    }
  }, [user, article.id, statusLoaded]);

  // Load user's reaction status from API
  const loadUserReactionStatus = async () => {
    try {
      const response = await userApi.checkArticleReactionStatus(article.id);
      if (response.success) {
        const { reaction_type, is_bookmarked } = response.data;
        setUserReaction(reaction_type || 'none');
        setIsBookmarked(is_bookmarked || false);
        setStatusLoaded(true);
      }
    } catch (error) {
      // Silent fail - user might not be logged in
      setStatusLoaded(true);
    }
  };

  // Calculate reading time
  const calculateReadingTime = (content) => {
    const wordsPerMinute = 200;
    const words = content?.split(' ').length || 0;
    return Math.ceil(words / wordsPerMinute);
  };

  const handleClick = () => {
    navigate(`/articles/${article.id}`);
  };

  const handleAuthorClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    navigate(`/profile/${article.author_id}`);
  };

  const handleEdit = (e) => {
    e.preventDefault();
    e.stopPropagation();
    onEdit && onEdit(article);
  };

  const handleDelete = (e) => {
    e.preventDefault();
    e.stopPropagation();
    onDelete && onDelete(article);
  };

  // Handle like toggle
  const handleLike = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!user) {
      toast.error('Please login to like articles');
      return;
    }

    try {
      setReactionLoading(true);
      
      if (userReaction === 'like') {
        const response = await userApi.unlikeArticle(article.id);
        if (response.success) {
          setUserReaction('none');
          setLikesCount(prev => prev - 1);
        }
      } else {
        const response = await userApi.likeArticle(article.id);
        if (response.success) {
          setUserReaction('like');
          setLikesCount(prev => prev + 1);
        }
      }
      
      // Call parent handler if provided
      onLike && onLike(article.id);
    } catch (error) {
      toast.error('Failed to update like status');
    } finally {
      setReactionLoading(false);
    }
  };

  // Handle dislike
  const handleDislike = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!user) {
      toast.error('Please login to interact with articles');
      return;
    }

    onDislike && onDislike(article.id);
  };

  // Handle bookmark toggle
  const handleBookmark = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!user) {
      toast.error('Please login to bookmark articles');
      return;
    }

    try {
      if (isBookmarked) {
        const response = await userApi.unbookmarkArticle(article.id);
        if (response.success) {
          setIsBookmarked(false);
          toast.success('Bookmark removed');
        }
      } else {
        const response = await userApi.bookmarkArticle(article.id);
        if (response.success) {
          setIsBookmarked(true);
          toast.success('Article bookmarked!');
        }
      }
    } catch (error) {
      toast.error('Failed to update bookmark');
    }
  };

  // Layout variants
  const layoutClasses = {
    grid: 'bg-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden border border-gray-100 hover:border-blue-200',
    list: 'bg-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden border border-gray-100 hover:border-blue-200 flex',
    featured: 'bg-white rounded-2xl shadow-xl hover:shadow-2xl transition-all duration-300 overflow-hidden border border-gray-100 hover:border-blue-200'
  };

  // Featured layout for hero articles
  if (layout === 'featured') {
    return (
      <motion.article
        whileHover={{ y: -4 }}
        className={`${layoutClasses[layout]} ${className}`}
      >
        <div onClick={handleClick} className="block cursor-pointer">
          {/* Large Image */}
          {article.image && (
            <div className="aspect-[16/9] overflow-hidden">
              <LazyLoadImage
                src={article.image}
                alt={article.title}
                className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
                effect="opacity"
              />
            </div>
          )}
          
          <div className="p-8">
            {/* Tags */}
            {article.tags && article.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-4">
                {article.tags.slice(0, 3).map((tag, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
                  >
                    <TagIcon className="w-3 h-3 mr-1" />
                    {tag}
                  </span>
                ))}
              </div>
            )}
            
            {/* Title */}
            <h2 className="text-3xl font-bold text-gray-900 mb-4 line-clamp-2 hover:text-blue-600 transition-colors">
              {article.title}
            </h2>
            
            {/* Abstract */}
            {(article.abstract || article.content) && (
              <p className="text-lg text-gray-600 mb-6 line-clamp-3">
                {truncateText(article.abstract || article.content, 200)}
              </p>
            )}
            
            {/* Author & Meta */}
            <div className="flex items-center justify-between">
              {showAuthor && (
                <div className="flex items-center space-x-3" onClick={handleAuthorClick}>
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-medium cursor-pointer">
                    {(article.author_name || article.author?.full_name)?.charAt(0).toUpperCase() || <UserIcon className="w-5 h-5" />}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 cursor-pointer hover:text-blue-600">
                      {article.author_name || article.author?.full_name || 'Unknown Author'}
                    </p>
                    <p className="text-sm text-gray-500">
                      {formatDistanceToNow(new Date(article.created_at), { addSuffix: true })}
                    </p>
                  </div>
                </div>
              )}
              
              <div className="flex items-center space-x-6 text-sm text-gray-500">
                <span className="flex items-center">
                  <ClockIcon className="w-4 h-4 mr-1" />
                  {calculateReadingTime(article.content)} min
                </span>
                <span className="flex items-center">
                  <EyeIcon className="w-4 h-4 mr-1" />
                  {formatNumber(article.views || 0)}
                </span>
                <span className="flex items-center">
                  <HeartIcon className="w-4 h-4 mr-1" />
                  {formatNumber(likesCount)}
                </span>
              </div>
            </div>
          </div>
        </div>
        
        {/* Action Buttons */}
        {showActions && (
          <div className="px-8 pb-6 flex justify-between items-center">
            <div className="flex space-x-2">
              <button
                onClick={handleLike}
                disabled={reactionLoading}
                className={`p-2 rounded-full transition-all duration-200 transform hover:scale-110 ${
                  userReaction === 'like'
                    ? 'bg-red-100 text-red-600 shadow-md'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200 hover:shadow-md'
                }`}
              >
                {userReaction === 'like' ? (
                  <HeartSolidIcon className="w-5 h-5" />
                ) : (
                  <HeartIcon className="w-5 h-5" />
                )}
              </button>
              
              <button
                onClick={handleBookmark}
                className={`p-2 rounded-full transition-all duration-200 transform hover:scale-110 ${
                  isBookmarked
                    ? 'bg-yellow-100 text-yellow-600 shadow-md'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200 hover:shadow-md'
                }`}
              >
                {isBookmarked ? (
                  <BookmarkSolidIcon className="w-5 h-5" />
                ) : (
                  <BookmarkIcon className="w-5 h-5" />
                )}
              </button>
              
              {user && canEditArticle && canEditArticle(article) && (
                <>
                  <button
                    onClick={handleEdit}
                    className="p-2 rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors"
                  >
                    <PencilIcon className="w-5 h-5" />
                  </button>
                  
                  <button
                    onClick={handleDelete}
                    className="p-2 rounded-full bg-red-100 text-red-600 hover:bg-red-200 transition-colors"
                  >
                    <TrashIcon className="w-5 h-5" />
                  </button>
                </>
              )}
            </div>
            
            <div onClick={handleClick} className="cursor-pointer">
              <span className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                Read Article
              </span>
            </div>
          </div>
        )}
      </motion.article>
    );
  }

  // List layout
  if (layout === 'list') {
    return (
      <motion.article
        whileHover={{ x: 4 }}
        className={`${layoutClasses[layout]} ${className}`}
      >
        <div onClick={handleClick} className="flex w-full cursor-pointer">
          {/* Content */}
          <div className="flex-1 p-6">
            {/* Tags */}
            {article.tags && article.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mb-2">
                {article.tags.slice(0, 2).map((tag, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
            
            {/* Title */}
            <h3 className="text-xl font-semibold text-gray-900 mb-2 line-clamp-2 hover:text-blue-600 transition-colors">
              {article.title}
            </h3>
            
            {/* Abstract */}
            {(article.abstract || article.content) && (
              <p className="text-gray-600 mb-4 line-clamp-2">
                {truncateText(article.abstract || article.content, 150)}
              </p>
            )}
            
            {/* Meta Info */}
            <div className="flex items-center justify-between">
              {showAuthor && (
                <div className="flex items-center space-x-2" onClick={handleAuthorClick}>
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-sm font-medium cursor-pointer">
                    {(article.author_name || article.author?.full_name)?.charAt(0).toUpperCase() || <UserIcon className="w-4 h-4" />}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900 cursor-pointer hover:text-blue-600">
                      {article.author_name || article.author?.full_name || 'Unknown Author'}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatDate(article.created_at)}
                    </p>
                  </div>
                </div>
              )}
              
              <div className="flex items-center space-x-4 text-xs text-gray-500">
                <span className="flex items-center">
                  <ClockIcon className="w-3 h-3 mr-1" />
                  {calculateReadingTime(article.content)} min
                </span>
                <span className="flex items-center">
                  <EyeIcon className="w-3 h-3 mr-1" />
                  {formatNumber(article.views || 0)}
                </span>
                <span className="flex items-center">
                  <HeartIcon className="w-3 h-3 mr-1" />
                  {formatNumber(likesCount)}
                </span>
              </div>
            </div>
          </div>
          
          {/* Image */}
          {article.image && (
            <div className="w-48 flex-shrink-0">
              <LazyLoadImage
                src={article.image}
                alt={article.title}
                className="w-full h-full object-cover"
                effect="opacity"
              />
            </div>
          )}
        </div>
        
        {/* Action Buttons */}
        {showActions && (
          <div className="px-6 pb-4 flex space-x-2">
            <button
              onClick={handleLike}
              disabled={reactionLoading}
              className={`p-1.5 rounded-full transition-colors ${
                userReaction === 'like'
                  ? 'bg-red-100 text-red-600'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {userReaction === 'like' ? (
                <HeartSolidIcon className="w-4 h-4" />
              ) : (
                <HeartIcon className="w-4 h-4" />
              )}
            </button>
            
            <button
              onClick={handleBookmark}
              className={`p-1.5 rounded-full transition-colors ${
                isBookmarked
                  ? 'bg-yellow-100 text-yellow-600'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {isBookmarked ? (
                <BookmarkSolidIcon className="w-4 h-4" />
              ) : (
                <BookmarkIcon className="w-4 h-4" />
              )}
            </button>
            
            {user && canEditArticle && canEditArticle(article) && (
              <>
                <button
                  onClick={handleEdit}
                  className="p-1.5 rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors"
                >
                  <PencilIcon className="w-4 h-4" />
                </button>
                
                <button
                  onClick={handleDelete}
                  className="p-1.5 rounded-full bg-red-100 text-red-600 hover:bg-red-200 transition-colors"
                >
                  <TrashIcon className="w-4 h-4" />
                </button>
              </>
            )}
          </div>
        )}
      </motion.article>
    );
  }

  // Default grid layout
  return (
    <motion.article
      whileHover={{ y: -4 }}
      className={`${layoutClasses[layout]} ${className}`}
    >
      <div onClick={handleClick} className="block cursor-pointer">
        {/* Image */}
        {article.image && (
          <div className="aspect-video overflow-hidden">
            <LazyLoadImage
              src={article.image}
              alt={article.title}
              className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
              effect="opacity"
            />
          </div>
        )}
        
        <div className="p-6">
          {/* Tags */}
          {article.tags && article.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-3">
              {article.tags.slice(0, 2).map((tag, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
          
          {/* Title */}
          <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2 hover:text-blue-600 transition-colors">
            {article.title}
          </h3>
          
          {/* Abstract */}
          {(article.abstract || article.content) && (
            <p className="text-gray-600 text-sm mb-4 line-clamp-3">
              {truncateText(article.abstract || article.content, 150)}
            </p>
          )}
          
          {/* Author & Meta */}
          {showAuthor && (
            <div className="flex items-center space-x-3 mb-4" onClick={handleAuthorClick}>
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-sm font-medium cursor-pointer">
                {(article.author_name || article.author?.full_name)?.charAt(0).toUpperCase() || <UserIcon className="w-4 h-4" />}
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900 cursor-pointer hover:text-blue-600">
                  {article.author_name || article.author?.full_name || 'Unknown Author'}
                </p>
                <p className="text-xs text-gray-500">
                  {formatDistanceToNow(new Date(article.created_at), { addSuffix: true })}
                </p>
              </div>
            </div>
          )}
          
          {/* Stats */}
          <div className="flex items-center justify-between text-xs text-gray-500">
            <div className="flex items-center space-x-3">
              <span className="flex items-center">
                <ClockIcon className="w-3 h-3 mr-1" />
                {calculateReadingTime(article.content)} min
              </span>
              <span className="flex items-center">
                <EyeIcon className="w-3 h-3 mr-1" />
                {formatNumber(article.views || 0)}
              </span>
              <span className="flex items-center">
                <HeartIcon className="w-3 h-3 mr-1" />
                {formatNumber(likesCount)}
              </span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Action Buttons */}
      {showActions && (
        <div className="px-6 pb-4 flex justify-between items-center border-t pt-4">
          <div className="flex space-x-2">
            <button
              onClick={handleLike}
              disabled={reactionLoading}
              className={`p-2 rounded-full transition-all duration-200 transform hover:scale-110 ${
                userReaction === 'like'
                  ? 'bg-red-100 text-red-600 shadow-md'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200 hover:shadow-md'
              }`}
            >
              {userReaction === 'like' ? (
                <HeartSolidIcon className="w-4 h-4" />
              ) : (
                <HeartIcon className="w-4 h-4" />
              )}
            </button>
            
            <button
              onClick={handleBookmark}
              className={`p-2 rounded-full transition-all duration-200 transform hover:scale-110 ${
                isBookmarked
                  ? 'bg-yellow-100 text-yellow-600 shadow-md'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200 hover:shadow-md'
              }`}
            >
              {isBookmarked ? (
                <BookmarkSolidIcon className="w-4 h-4" />
              ) : (
                <BookmarkIcon className="w-4 h-4" />
              )}
            </button>
            
            {user && canEditArticle && canEditArticle(article) && (
              <>
                <button
                  onClick={handleEdit}
                  className="p-2 rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors"
                >
                  <PencilIcon className="w-4 h-4" />
                </button>
                
                <button
                  onClick={handleDelete}
                  className="p-2 rounded-full bg-red-100 text-red-600 hover:bg-red-200 transition-colors"
                >
                  <TrashIcon className="w-4 h-4" />
                </button>
              </>
            )}
          </div>
          
          <span className="text-xs text-gray-500">
            {formatDate(article.created_at)}
          </span>
        </div>
      )}
    </motion.article>
  );
};

export default ArticleCard;
