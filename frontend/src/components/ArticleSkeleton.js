import React from 'react';

const ArticleSkeleton = () => {
  return (
    <div className="min-h-screen" style={{ background: 'var(--bg)' }}>
      <div className="max-w-4xl mx-auto shadow-sm bg-surface border-surface" style={{ borderWidth: 1 }}>
        {/* Hero Image Skeleton */}
        <div className="w-full h-96 bg-gray-200 animate-pulse" />

        <div className="px-6 py-8 lg:px-12">
          {/* Tags Skeleton */}
          <div className="flex gap-2 mb-4">
            <div className="h-6 w-16 bg-gray-200 rounded-full animate-pulse" />
            <div className="h-6 w-20 bg-gray-200 rounded-full animate-pulse" />
            <div className="h-6 w-14 bg-gray-200 rounded-full animate-pulse" />
          </div>

          {/* Title Skeleton */}
          <div className="space-y-3 mb-4">
            <div className="h-8 bg-gray-200 rounded animate-pulse" />
            <div className="h-8 bg-gray-200 rounded w-3/4 animate-pulse" />
          </div>

          {/* Abstract Skeleton */}
          <div className="space-y-2 mb-6">
            <div className="h-6 bg-gray-200 rounded animate-pulse" />
            <div className="h-6 bg-gray-200 rounded w-5/6 animate-pulse" />
          </div>

          {/* Author Card Skeleton */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-gray-200 rounded-full animate-pulse" />
              <div className="space-y-2">
                <div className="h-4 w-24 bg-gray-200 rounded animate-pulse" />
                <div className="h-3 w-32 bg-gray-200 rounded animate-pulse" />
              </div>
            </div>
            <div className="h-8 w-20 bg-gray-200 rounded animate-pulse" />
          </div>

          {/* Content Skeleton */}
          <div className="space-y-4 mb-8">
            {Array.from({ length: 8 }).map((_, index) => (
              <div key={index} className="space-y-2">
                <div className="h-4 bg-gray-200 rounded animate-pulse" />
                <div className="h-4 bg-gray-200 rounded w-11/12 animate-pulse" />
                <div className="h-4 bg-gray-200 rounded w-4/5 animate-pulse" />
              </div>
            ))}
          </div>

          {/* Action Buttons Skeleton */}
          <div className="flex items-center justify-between py-6 border-t border-gray-200">
            <div className="flex space-x-4">
              <div className="h-10 w-20 bg-gray-200 rounded-lg animate-pulse" />
              <div className="h-10 w-20 bg-gray-200 rounded-lg animate-pulse" />
              <div className="h-10 w-24 bg-gray-200 rounded-lg animate-pulse" />
            </div>
            <div className="h-10 w-20 bg-gray-200 rounded-lg animate-pulse" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ArticleSkeleton;
