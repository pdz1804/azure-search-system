import React from 'react';
import { Link } from 'react-router-dom';
import { LazyLoadImage } from 'react-lazy-load-image-component';
import { UserPlusIcon, CheckIcon } from '@heroicons/react/24/outline';
import { format } from 'date-fns';

const AuthorCard = ({ 
  author, 
  article, 
  isFollowing, 
  onFollow, 
  canFollow,
  size = 'medium' // 'small', 'medium', 'large'
}) => {
  if (!author) return null;

  const sizeClasses = {
    small: {
      avatar: 'w-8 h-8',
      text: 'text-sm',
      button: 'px-2 py-1 text-xs'
    },
    medium: {
      avatar: 'w-12 h-12',
      text: 'text-base',
      button: 'px-3 py-1.5 text-sm'
    },
    large: {
      avatar: 'w-16 h-16',
      text: 'text-lg',
      button: 'px-4 py-2 text-base'
    }
  };

  const classes = sizeClasses[size];

  return (
    <div className="flex items-center space-x-3">
      {/* Author Avatar */}
      <Link to={`/profile/${author.id}`} className="flex-shrink-0">
        {author.avatar_url ? (
          <LazyLoadImage
            src={author.avatar_url}
            alt={author.full_name}
            className={`${classes.avatar} rounded-full object-cover`}
            effect="opacity"
          />
        ) : (
          <div className={`${classes.avatar} bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-medium`}>
            {author.full_name?.charAt(0).toUpperCase()}
          </div>
        )}
      </Link>

      {/* Author Info */}
      <div className="flex-1 min-w-0">
        <Link 
          to={`/profile/${author.id}`}
          className={`font-medium text-gray-900 hover:text-blue-600 transition-colors ${classes.text}`}
        >
          {author.full_name}
        </Link>
        
        {article?.created_at && (
          <p className="text-gray-500 text-sm">
            Published on {format(new Date(article.created_at), 'MMM dd, yyyy')}
          </p>
        )}
        
        {author.role && author.role !== 'user' && (
          <span className="inline-block mt-1 px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded-full capitalize">
            {author.role}
          </span>
        )}
      </div>

      {/* Follow Button */}
      {canFollow && (
        <button
          onClick={onFollow}
          className={`flex items-center space-x-1 rounded-lg font-medium transition-colors ${classes.button} ${
            isFollowing
              ? 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {isFollowing ? (
            <>
              <CheckIcon className="w-4 h-4" />
              <span>Following</span>
            </>
          ) : (
            <>
              <UserPlusIcon className="w-4 h-4" />
              <span>Follow</span>
            </>
          )}
        </button>
      )}
    </div>
  );
};

export default AuthorCard;
