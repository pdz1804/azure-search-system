import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
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
  SunIcon,
  MoonIcon,
  HomeIcon,
  NewspaperIcon,
  UserGroupIcon,
  DocumentTextIcon,
  HeartIcon
} from '@heroicons/react/24/outline';
import { BellIcon as BellSolidIcon } from '@heroicons/react/24/solid';
import toast from 'react-hot-toast';

import { useAuth } from '../context/AuthContext';
import { userApi } from '../api/userApi';
import LoadingSpinner from './LoadingSpinner';

const Header = ({ 
  onSearch, 
  searchValue = '', 
  darkMode = false, 
  onToggleDarkMode 
}) => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  const [searchQuery, setSearchQuery] = useState(searchValue);
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [notificationsLoading, setNotificationsLoading] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  
  const searchRef = useRef(null);
  const userMenuRef = useRef(null);
  const notificationRef = useRef(null);

  // Navigation items
  const navigationItems = [
    { name: 'Home', href: '/', icon: HomeIcon },
    { name: 'Articles', href: '/articles', icon: NewspaperIcon },
    { name: 'Authors', href: '/authors', icon: UserGroupIcon },
  ];

  // Handle search
  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      onSearch && onSearch(searchQuery.trim());
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  // Handle logout
  const handleLogout = async () => {
    try {
      await logout();
      toast.success('Logged out successfully');
      navigate('/');
    } catch (error) {
      toast.error('Error logging out');
    }
    setShowUserMenu(false);
  };

  // Load notifications
  const loadNotifications = async () => {
    if (!user) return;
    
    try {
      setNotificationsLoading(true);
      const response = await userApi.getNotifications();
      if (response.success) {
        setNotifications(response.data);
        setUnreadCount(response.data.filter(n => !n.read).length);
      }
    } catch (error) {
      console.error('Failed to load notifications:', error);
    } finally {
      setNotificationsLoading(false);
    }
  };

  // Mark notification as read
  const markAsRead = async (notificationId) => {
    try {
      const response = await userApi.markNotificationRead(notificationId);
      if (response.success) {
        setNotifications(prev => 
          prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
        );
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  // Close menus when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setShowUserMenu(false);
      }
      if (notificationRef.current && !notificationRef.current.contains(event.target)) {
        setShowNotifications(false);
      }
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setIsSearchFocused(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Load notifications when user is available
  useEffect(() => {
    if (user && showNotifications) {
      loadNotifications();
    }
  }, [user, showNotifications]);

  return (
    <header className="bg-white shadow-sm border-b sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo and Brand */}
          <div className="flex items-center">
            <Link 
              to="/" 
              className="flex items-center space-x-2 text-2xl font-bold text-gray-900 hover:text-blue-600 transition-colors"
            >
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <NewspaperIcon className="w-5 h-5 text-white" />
              </div>
              <span>ArticleHub</span>
            </Link>
          </div>

          {/* Navigation - Desktop */}
          <nav className="hidden md:flex items-center space-x-8">
            {navigationItems.map((item) => {
              const isActive = location.pathname === item.href;
              const IconComponent = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'text-blue-600 bg-blue-50'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  <IconComponent className="w-4 h-4" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>

          {/* Search Bar */}
          <div className="flex-1 max-w-lg mx-8" ref={searchRef}>
            <form onSubmit={handleSearch} className="relative">
              <div className={`relative transition-all duration-200 ${
                isSearchFocused ? 'transform scale-105' : ''
              }`}>
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search articles, authors..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onFocus={() => setIsSearchFocused(true)}
                  className={`w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all ${
                    isSearchFocused ? 'bg-gray-50' : 'bg-white'
                  }`}
                />
              </div>
              
              {/* Search Suggestions */}
              <AnimatePresence>
                {isSearchFocused && searchQuery && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="absolute top-full left-0 right-0 bg-white border rounded-lg shadow-lg mt-1 max-h-64 overflow-y-auto"
                  >
                    <div className="p-2 text-sm text-gray-500">
                      Press Enter to search for "{searchQuery}"
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </form>
          </div>

          {/* Right Side Actions */}
          <div className="flex items-center space-x-4">
            {/* Dark Mode Toggle */}
            {onToggleDarkMode && (
              <button
                onClick={onToggleDarkMode}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              >
                {darkMode ? (
                  <SunIcon className="w-5 h-5" />
                ) : (
                  <MoonIcon className="w-5 h-5" />
                )}
              </button>
            )}

            {isAuthenticated() ? (
              <>
                {/* Create Article Button - Writers and Admins */}
                {(user?.role === 'writer' || user?.role === 'admin') && (
                  <Link
                    to="/write"
                    className="flex items-center space-x-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <PlusIcon className="w-4 h-4" />
                    <span className="hidden sm:inline">Write</span>
                  </Link>
                )}

                {/* Notifications */}
                <div className="relative" ref={notificationRef}>
                  <button
                    onClick={() => setShowNotifications(!showNotifications)}
                    className="relative p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    {unreadCount > 0 ? (
                      <BellSolidIcon className="w-5 h-5" />
                    ) : (
                      <BellIcon className="w-5 h-5" />
                    )}
                    {unreadCount > 0 && (
                      <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                        {unreadCount > 9 ? '9+' : unreadCount}
                      </span>
                    )}
                  </button>

                  {/* Notifications Dropdown */}
                  <AnimatePresence>
                    {showNotifications && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: -10 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: -10 }}
                        className="absolute right-0 top-full mt-2 w-80 bg-white border rounded-lg shadow-lg overflow-hidden"
                      >
                        <div className="p-4 border-b bg-gray-50">
                          <h3 className="font-semibold text-gray-900">Notifications</h3>
                        </div>
                        
                        <div className="max-h-64 overflow-y-auto">
                          {notificationsLoading ? (
                            <div className="p-4 flex justify-center">
                              <LoadingSpinner size="sm" />
                            </div>
                          ) : notifications.length > 0 ? (
                            notifications.map((notification) => (
                              <div
                                key={notification.id}
                                onClick={() => markAsRead(notification.id)}
                                className={`p-4 border-b hover:bg-gray-50 cursor-pointer ${
                                  !notification.read ? 'bg-blue-50' : ''
                                }`}
                              >
                                <p className="text-sm text-gray-900">{notification.message}</p>
                                <p className="text-xs text-gray-500 mt-1">{notification.created_at}</p>
                              </div>
                            ))
                          ) : (
                            <div className="p-4 text-center text-gray-500">
                              No notifications yet
                            </div>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {/* User Menu */}
                <div className="relative" ref={userMenuRef}>
                  <button
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className="flex items-center space-x-2 p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-medium">
                      {user?.full_name?.charAt(0).toUpperCase() || <UserIcon className="w-4 h-4" />}
                    </div>
                    <span className="hidden md:inline font-medium">{user?.full_name}</span>
                  </button>

                  {/* User Dropdown */}
                  <AnimatePresence>
                    {showUserMenu && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: -10 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: -10 }}
                        className="absolute right-0 top-full mt-2 w-48 bg-white border rounded-lg shadow-lg overflow-hidden"
                      >
                        <div className="p-4 border-b bg-gray-50">
                          <p className="font-medium text-gray-900">{user?.full_name}</p>
                          <p className="text-sm text-gray-500">{user?.email}</p>
                          <div className="flex items-center mt-1">
                            <span className={`text-xs px-2 py-1 rounded-full ${
                              user?.role === 'admin' 
                                ? 'bg-red-100 text-red-800' 
                                : user?.role === 'writer'
                                ? 'bg-blue-100 text-blue-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}>
                              {user?.role?.toUpperCase()}
                            </span>
                          </div>
                        </div>
                        
                        <div className="py-2">
                          <Link
                            to="/profile"
                            onClick={() => setShowUserMenu(false)}
                            className="flex items-center space-x-2 px-4 py-2 text-gray-700 hover:bg-gray-50"
                          >
                            <UserIcon className="w-4 h-4" />
                            <span>Profile</span>
                          </Link>
                          
                          <Link
                            to="/bookmarks"
                            onClick={() => setShowUserMenu(false)}
                            className="flex items-center space-x-2 px-4 py-2 text-gray-700 hover:bg-gray-50"
                          >
                            <BookmarkIcon className="w-4 h-4" />
                            <span>Bookmarks</span>
                          </Link>

                          {(user?.role === 'writer' || user?.role === 'admin') && (
                            <>
                              <Link
                                to="/my-articles"
                                onClick={() => setShowUserMenu(false)}
                                className="flex items-center space-x-2 px-4 py-2 text-gray-700 hover:bg-gray-50"
                              >
                                <DocumentTextIcon className="w-4 h-4" />
                                <span>My Articles</span>
                              </Link>
                              
                              <Link
                                to="/dashboard"
                                onClick={() => setShowUserMenu(false)}
                                className="flex items-center space-x-2 px-4 py-2 text-gray-700 hover:bg-gray-50"
                              >
                                <CogIcon className="w-4 h-4" />
                                <span>Dashboard</span>
                              </Link>
                            </>
                          )}
                        </div>
                        
                        <div className="border-t py-2">
                          <button
                            onClick={handleLogout}
                            className="flex items-center space-x-2 w-full px-4 py-2 text-red-600 hover:bg-red-50"
                          >
                            <ArrowRightOnRectangleIcon className="w-4 h-4" />
                            <span>Logout</span>
                          </button>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </>
            ) : (
              /* Guest Actions */
              <div className="flex items-center space-x-2">
                <Link
                  to="/login"
                  state={{ from: location }}
                  className="px-4 py-2 text-gray-600 hover:text-gray-900 font-medium transition-colors"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Sign Up
                </Link>
              </div>
            )}

            {/* Mobile Menu Button */}
            <button
              onClick={() => setShowMobileMenu(!showMobileMenu)}
              className="md:hidden p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
            >
              {showMobileMenu ? (
                <XMarkIcon className="w-5 h-5" />
              ) : (
                <Bars3Icon className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        <AnimatePresence>
          {showMobileMenu && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="md:hidden border-t bg-white"
            >
              <div className="py-4 space-y-2">
                {navigationItems.map((item) => {
                  const isActive = location.pathname === item.href;
                  const IconComponent = item.icon;
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      onClick={() => setShowMobileMenu(false)}
                      className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors ${
                        isActive
                          ? 'text-blue-600 bg-blue-50'
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                      }`}
                    >
                      <IconComponent className="w-5 h-5" />
                      <span>{item.name}</span>
                    </Link>
                  );
                })}
                
                {!isAuthenticated() && (
                  <div className="border-t pt-4 mt-4 space-y-2">
                    <Link
                      to="/login"
                      state={{ from: location }}
                      onClick={() => setShowMobileMenu(false)}
                      className="block px-4 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-md"
                    >
                      Login
                    </Link>
                    <Link
                      to="/register"
                      onClick={() => setShowMobileMenu(false)}
                      className="block px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                    >
                      Sign Up
                    </Link>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </header>
  );
};

export default Header;
