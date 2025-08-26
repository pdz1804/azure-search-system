import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import {
  MagnifyingGlassIcon,
  BellIcon,
  UserIcon,
  Bars3Icon,
  XMarkIcon,
  PlusIcon,
  BookmarkIcon,
  CogIcon,
  ArrowRightOnRectangleIcon,
  HomeIcon,
  DocumentTextIcon,
  EnvelopeIcon,
  HeartIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../context/AuthContext';

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isProfileDropdownOpen, setIsProfileDropdownOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const { user, isAuthenticated, logout, hasRole } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const profileDropdownRef = useRef(null);

  const navigationItems = [
    { name: 'Home', href: '/', icon: HomeIcon },
    { name: 'Blogs', href: '/blogs', icon: DocumentTextIcon },
    { name: 'About', href: '/about', icon: DocumentTextIcon },
    { name: 'Contact', href: '/contact', icon: EnvelopeIcon },
  ];

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const toggleProfileDropdown = () => {
    setIsProfileDropdownOpen(!isProfileDropdownOpen);
  };

  const closeProfileDropdown = () => {
    setIsProfileDropdownOpen(false);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (profileDropdownRef.current && !profileDropdownRef.current.contains(event.target)) {
        closeProfileDropdown();
      }
    };

    const handleEscapeKey = (event) => {
      if (event.key === 'Escape') {
        closeProfileDropdown();
      }
    };

    if (isProfileDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscapeKey);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscapeKey);
    };
  }, [isProfileDropdownOpen]);

  // Close dropdown on route change
  useEffect(() => {
    closeProfileDropdown();
  }, [location.pathname]);

  // theme toggle removed - single theme only

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
      setSearchQuery('');
      setIsMenuOpen(false);
    }
  };

  const handleSearchKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch(e);
    }
  };

  const isActive = (href) => {
    if (href === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(href);
  };

  return (
  <header className="site-header backdrop-blur-md shadow-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex-shrink-0">
            <Link to="/" className="flex items-center space-x-2 group">
              <div className="w-8 h-8 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-lg flex items-center justify-center shadow-lg group-hover:shadow-xl transition-all duration-300">
                <DocumentTextIcon className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                ArticleHub
              </span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex ml-6 space-x-8">
            {navigationItems.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center space-x-1 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                      isActive(item.href)
                        ? 'text-indigo-600 bg-indigo-50 border border-indigo-200'
                        : 'text-gray-600 hover:text-indigo-600 hover:bg-indigo-50'
                    }`}
              >
                <item.icon className="w-4 h-4" />
                <span>{item.name}</span>
              </Link>
            ))}
          </nav>

          {/* Search Bar */}
          <div className="hidden md:flex flex-1 max-w-sm lg:max-w-md mx-4 lg:mx-8">
            <form onSubmit={handleSearch} className="relative w-full">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <MagnifyingGlassIcon className="h-4 w-4 lg:h-5 lg:w-5 text-gray-400" />
              </div>
              <input
                type="text"
                placeholder="Search articles, authors..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleSearchKeyPress}
                className="block w-full pl-9 lg:pl-10 pr-10 lg:pr-12 py-1.5 lg:py-2 border border-gray-200 rounded-lg bg-gray-50 text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200"
              />
              <button
                type="submit"
                onClick={handleSearch}
                className="absolute inset-y-0 right-0 pr-3 flex items-center hover:bg-indigo-50 rounded-r-lg transition-colors duration-200"
              >
                <MagnifyingGlassIcon className="h-4 w-4 lg:h-5 lg:w-5 text-gray-400 hover:text-indigo-600 transition-colors duration-200" />
              </button>
            </form>
          </div>

          {/* Right Side Actions */}
            <div className="flex items-center space-x-4">
              {/* theme toggle removed */}

            {/* Write Button - Only for admin and writer */}
            {isAuthenticated() && (user?.role === 'admin' || user?.role === 'writer') && (
              <button
                onClick={() => navigate('/write')}
                className="hidden sm:flex items-center space-x-1 lg:space-x-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-3 lg:px-4 py-1.5 lg:py-2 rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 shadow-md hover:shadow-lg text-sm lg:text-base"
              >
                <PlusIcon className="w-3 h-3 lg:w-4 lg:h-4" />
                <span className="hidden lg:inline">Write</span>
                <span className="lg:hidden">+</span>
              </button>
            )}

            {/* User Menu */}
            {isAuthenticated() ? (
              <div className="relative" ref={profileDropdownRef}>
                <button
                  onClick={toggleProfileDropdown}
                    className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 transition-all duration-200"
                >
                  {user?.avatar_url ? (
                    <img
                      src={user.avatar_url}
                      alt={user?.full_name || 'User avatar'}
                      className="w-7 h-7 lg:w-8 lg:h-8 rounded-full object-cover border border-gray-200"
                    />
                  ) : (
                    <div className="w-7 h-7 lg:w-8 lg:h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-medium text-xs lg:text-sm">
                      {user?.full_name?.[0] || user?.email?.[0] || 'U'}
                    </div>
                  )}
                    <span className="hidden md:block text-sm font-medium text-gray-700 max-w-24 lg:max-w-none truncate">
                    {user?.full_name || user?.email || 'User'}
                  </span>
                </button>

                {/* Dropdown Menu */}
                  {isProfileDropdownOpen && (
                  <div className="absolute right-0 mt-2 w-48 dropdown-panel rounded-lg shadow-lg border py-1 z-50">
                    <Link
                      to="/profile"
                      onClick={closeProfileDropdown}
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-indigo-50 hover:text-indigo-600 transition-colors duration-200"
                    >
                      <UserIcon className="w-4 h-4 inline mr-2" />
                      Profile
                    </Link>
                    {(user?.role === 'admin' || user?.role === 'writer') && (
                      <Link
                        to="/my-articles"
                        onClick={closeProfileDropdown}
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-indigo-50 hover:text-indigo-600 transition-colors duration-200"
                      >
                        <DocumentTextIcon className="w-4 h-4 inline mr-2" />
                        My Articles
                      </Link>
                    )}
                    <Link
                      to="/bookmarks"
                      onClick={closeProfileDropdown}
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-indigo-50 hover:text-indigo-600 transition-colors duration-200"
                    >
                      <BookmarkIcon className="w-4 h-4 inline mr-2" />
                      Bookmarks
                    </Link>
                    {user?.role === 'admin' && (
                      <Link
                        to="/dashboard"
                        onClick={closeProfileDropdown}
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-indigo-50 hover:text-indigo-600 transition-colors duration-200"
                      >
                        <CogIcon className="w-4 h-4 inline mr-2" />
                        Admin Dashboard
                      </Link>
                    )}
                    <hr className="my-1 border-gray-100" />
                    <button
                      onClick={() => {
                        handleLogout();
                        closeProfileDropdown();
                      }}
                      className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors duration-200"
                    >
                      <ArrowRightOnRectangleIcon className="w-4 h-4 inline mr-2" />
                      Logout
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center space-x-2 lg:space-x-3">
                <Link
                  to="/login"
                  className="text-gray-600 hover:text-indigo-600 font-medium transition-colors duration-200 text-sm lg:text-base"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-3 lg:px-4 py-1.5 lg:py-2 rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 shadow-md hover:shadow-lg text-sm lg:text-base"
                >
                  Sign Up
                </Link>
              </div>
            )}

            {/* Mobile Menu Button */}
            <button
              onClick={toggleMenu}
              className="md:hidden p-2 text-gray-600 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-all duration-200"
            >
              {isMenuOpen ? (
                <XMarkIcon className="h-6 w-6" />
              ) : (
                <Bars3Icon className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <div className="md:hidden py-4 border-t border-gray-100">
            <div className="space-y-2">
              {navigationItems.map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setIsMenuOpen(false)}
                  className={`block px-3 py-2 rounded-lg text-base font-medium transition-all duration-200 ${
                    isActive(item.href)
                      ? 'text-indigo-600 bg-indigo-50 border border-indigo-200'
                      : 'text-gray-600 hover:text-indigo-600 hover:bg-indigo-50'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <item.icon className="w-5 h-5" />
                    <span>{item.name}</span>
                  </div>
                </Link>
              ))}
            </div>
            
            {/* Mobile Search */}
            <div className="mt-4">
              <form onSubmit={handleSearch} className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  placeholder="Search articles, authors..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={handleSearchKeyPress}
                  className="block w-full pl-10 pr-12 py-2 border border-gray-200 rounded-lg bg-gray-50 text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
                <button
                  type="submit"
                  onClick={handleSearch}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center hover:bg-indigo-50 rounded-r-lg transition-colors duration-200"
                >
                  <MagnifyingGlassIcon className="h-5 w-5 text-gray-400 hover:text-indigo-600 transition-colors duration-200" />
                </button>
              </form>
            </div>

            {/* Mobile User Actions */}
            {isAuthenticated() && (user?.role === 'admin' || user?.role === 'writer') && (
              <div className="mt-4 space-y-2">
                <button
                  onClick={() => {
                    navigate('/write');
                    setIsMenuOpen(false);
                  }}
                  className="w-full flex items-center justify-center space-x-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-4 py-2 rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 transition-all duration-200"
                >
                  <PlusIcon className="w-4 h-4" />
                  <span>Write Article</span>
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
