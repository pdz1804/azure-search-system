import React, { useState, useEffect } from 'react';
import { message, Table, Button, Modal, Select, Tag, Input, Space, Drawer, Dropdown, Card, Row, Col, Statistic } from 'antd';
import { 
  UserIcon,
  CogIcon,
  ExclamationTriangleIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  ArrowPathIcon,
  Bars3Icon,
  EllipsisVerticalIcon,
  UsersIcon,
  ShieldCheckIcon,
  UserGroupIcon
} from '@heroicons/react/24/outline';
import { 
  UserIcon as UserSolid
} from '@heroicons/react/24/solid';
import { userApi } from '../api/userApi';
import { useAuth } from '../context/AuthContext';
import { formatNumber } from '../utils/helpers';
import { motion } from 'framer-motion';

const { Option } = Select;
const { Search } = Input;

/**
 * Admin Dashboard Component
 * Only accessible by admin users for user management
 */
const Dashboard = () => {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [deleteModalVisible, setDeleteModalVisible] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [editForm, setEditForm] = useState({ role: '', is_active: true });
  const [updating, setUpdating] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
    loading: false
  });
  
  // Search and filter states
  const [searchText, setSearchText] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortField, setSortField] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('descend');
  
  // Mobile responsive states
  const [isMobile, setIsMobile] = useState(false);
  const [filterDrawerVisible, setFilterDrawerVisible] = useState(false);

  useEffect(() => {
    fetchUsers(pagination.current, pagination.pageSize);
    checkScreenSize();
    
    const handleResize = () => checkScreenSize();
    window.addEventListener('resize', handleResize);
    
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const checkScreenSize = () => {
    setIsMobile(window.innerWidth < 768);
  };

  // Fetch users with pagination from backend
  const fetchUsers = async (page = 1, pageSize = 20) => {
    try {
      setLoading(true);
      setPagination(prev => ({ ...prev, loading: true }));
      
      const response = await userApi.getAllUsersAdmin(page, pageSize);
      
      if (response.success) {
        const usersData = response.data || [];
        const paginationData = response.pagination || {};
        
        setUsers(usersData);
        setFilteredUsers(usersData); // Initially set filtered to all users
        setPagination(prev => ({
          ...prev,
          current: page,
          pageSize: pageSize,
          total: paginationData.total_results || 0,
          loading: false
        }));
        
        console.log(`Admin Dashboard: Loaded ${usersData.length} users for page ${page}`);
        console.log(`Total users: ${paginationData.total_results || 0}`);
      } else {
        message.error('Failed to fetch users');
        setPagination(prev => ({ ...prev, loading: false }));
      }
    } catch (error) {
      message.error('Failed to load users');
      console.error('Error fetching users:', error);
      setPagination(prev => ({ ...prev, loading: false }));
    } finally {
      setLoading(false);
    }
  };

  // Apply filters to current page data only
  const applyFilters = () => {
    let filtered = [...users];

    // Apply search filter
    if (searchText) {
      const searchLower = searchText.toLowerCase();
      filtered = filtered.filter(user => 
        user.full_name?.toLowerCase().includes(searchLower) ||
        user.email?.toLowerCase().includes(searchLower)
      );
    }

    // Apply role filter
    if (roleFilter !== 'all') {
      filtered = filtered.filter(user => user.role === roleFilter);
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      const isActive = statusFilter === 'active';
      filtered = filtered.filter(user => (user.is_active !== false) === isActive);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue = a[sortField];
      let bValue = b[sortField];

      // Handle special cases
      if (sortField === 'created_at') {
        aValue = new Date(aValue || 0);
        bValue = new Date(bValue || 0);
      }

      if (sortOrder === 'ascend') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    setFilteredUsers(filtered);
  };

  // Apply filters whenever data or filters change (only on current page data)
  useEffect(() => {
    applyFilters();
  }, [users, searchText, roleFilter, statusFilter, sortField, sortOrder]);

  const handleEditUser = (user) => {
    setSelectedUser(user);
    setEditForm({
      role: user.role || 'user',
      is_active: user.is_active !== false
    });
    setEditModalVisible(true);
  };

  const handleDeleteUser = (user) => {
    setSelectedUser(user);
    setDeleteModalVisible(true);
  };

  const handleUpdateUser = async () => {
    if (!selectedUser) return;
    
    try {
      setUpdating(true);
      const response = await userApi.updateUser(selectedUser.id, editForm);
      if (response.success) {
        message.success('User updated successfully');
        setEditModalVisible(false);
        // Reload current page instead of all users
        fetchUsers(pagination.current, pagination.pageSize);
      } else {
        message.error('Failed to update user');
      }
    } catch (error) {
      message.error('Failed to update user');
      console.error('Error updating user:', error);
    } finally {
      setUpdating(false);
    }
  };

  const confirmDeleteUser = async () => {
    if (!selectedUser) return;
    
    try {
      setDeleting(true);
      const response = await userApi.deleteUser(selectedUser.id);
      if (response.success) {
        message.success('User deleted successfully');
        setDeleteModalVisible(false);
        setSelectedUser(null);
        // Reload current page instead of all users
        fetchUsers(pagination.current, pagination.pageSize);
      } else {
        message.error('Failed to delete user');
      }
    } catch (error) {
      message.error('Failed to delete user');
      console.error('Error deleting user:', error);
    } finally {
      setDeleting(false);
    }
  };

  const handleReactivateUser = async (user) => {
    try {
      const response = await userApi.updateUser(user.id, { is_active: true });
      if (response.success) {
        message.success('User reactivated successfully');
        // Reload current page instead of all users
        fetchUsers(pagination.current, pagination.pageSize);
      } else {
        message.error('Failed to reactivate user');
      }
    } catch (error) {
      message.error('Failed to reactivate user');
      console.error('Error reactivating user:', error);
    }
  };

  const handleTableChange = (paginationInfo, filters, sorter) => {
    // Handle pagination change - fetch new page data
    if (paginationInfo.current !== pagination.current || paginationInfo.pageSize !== pagination.pageSize) {
      fetchUsers(paginationInfo.current, paginationInfo.pageSize);
      return;
    }

    // Handle sorting
    if (sorter && sorter.field) {
      setSortField(sorter.field);
      setSortOrder(sorter.order || 'descend');
    }
  };

  const handleSearch = (value) => {
    setSearchText(value);
    // When searching, we need to go back to page 1 and refetch
    if (value !== searchText) {
      fetchUsers(1, pagination.pageSize);
    }
  };

  const handleRoleFilterChange = (value) => {
    setRoleFilter(value);
    // When filtering, we need to go back to page 1 and refetch
    fetchUsers(1, pagination.pageSize);
  };

  const handleStatusFilterChange = (value) => {
    setStatusFilter(value);
    // When filtering, we need to go back to page 1 and refetch
    fetchUsers(1, pagination.pageSize);
  };

  const clearFilters = () => {
    setSearchText('');
    setRoleFilter('all');
    setStatusFilter('all');
    setSortField('created_at');
    setSortOrder('descend');
    // Fetch first page with cleared filters
    fetchUsers(1, pagination.pageSize);
  };

  const getRoleColor = (role) => {
    switch (role) {
      case 'admin': return 'red';
      case 'writer': return 'blue';
      case 'user': return 'green';
      default: return 'gray';
    }
  };

  const getStatusColor = (isActive) => {
    return isActive !== false ? 'green' : 'red';
  };

  // Mobile-optimized columns
  const getMobileColumns = () => [
    {
      title: 'User',
      dataIndex: 'full_name',
      key: 'full_name',
      render: (text, record) => (
        <div className="space-y-2">
          <div className="flex items-center space-x-3">
            {record.avatar_url ? (
              <img 
                src={record.avatar_url} 
                alt={text}
                className="w-8 h-8 rounded-full object-cover"
              />
            ) : (
              <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                <UserIcon className="w-5 h-5 text-gray-500" />
              </div>
            )}
            <div className="min-w-0 flex-1">
              <div className="font-semibold text-gray-900 truncate">{text}</div>
              <div className="text-sm text-gray-500 truncate">{record.email}</div>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Tag color={getRoleColor(record.role)} className="capitalize text-xs">
              {record.role || 'user'}
            </Tag>
            <Tag color={getStatusColor(record.is_active)} className="text-xs">
              {record.is_active !== false ? 'Active' : 'Inactive'}
            </Tag>
          </div>
        </div>
      ),
    },
    {
      title: 'Stats',
      key: 'stats',
      render: (_, record) => (
        <div className="space-y-1 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-500">Articles:</span>
            <span className="font-medium">{record.articles_count || 0}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Views:</span>
            <span className="font-medium">{formatNumber(record.total_views || 0)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Joined:</span>
            <span className="font-medium">{record.created_at ? new Date(record.created_at).toLocaleDateString() : '-'}</span>
          </div>
        </div>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 80,
      render: (_, record) => (
        <Dropdown
          menu={{
            items: [
              {
                key: 'edit',
                label: 'Edit User',
                icon: <CogIcon className="w-4 h-4" />,
                onClick: () => handleEditUser(record)
              },
              ...(record.is_active === false && record.id !== user?.id ? [{
                key: 'reactivate',
                label: 'Reactivate',
                icon: <ArrowPathIcon className="w-4 h-4" />,
                onClick: () => handleReactivateUser(record)
              }] : []),
              ...(record.is_active !== false && record.id !== user?.id ? [{
                key: 'delete',
                label: 'Delete',
                icon: <ExclamationTriangleIcon className="w-4 h-4" />,
                onClick: () => handleDeleteUser(record)
              }] : [])
            ]
          }}
          trigger={['click']}
          placement="bottomRight"
        >
          <Button
            size="small"
            icon={<EllipsisVerticalIcon className="w-4 h-4" />}
            className="flex items-center justify-center"
          />
        </Dropdown>
      ),
    },
  ];

  // Desktop columns
  const getDesktopColumns = () => [
    {
      title: 'User',
      dataIndex: 'full_name',
      key: 'full_name',
      sorter: true,
      sortOrder: sortField === 'full_name' ? sortOrder : null,
      render: (text, record) => (
        <div className="flex items-center space-x-3">
          {record.avatar_url ? (
            <img 
              src={record.avatar_url} 
              alt={text}
              className="w-8 h-8 rounded-full object-cover"
            />
          ) : (
            <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
              <UserIcon className="w-4 h-4 text-gray-500" />
            </div>
          )}
          <div className="min-w-0 flex-1">
            <div className="font-medium text-gray-900 truncate">{text}</div>
            <div className="text-sm text-gray-500 truncate">{record.email}</div>
          </div>
        </div>
      ),
    },
    {
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      sorter: true,
      sortOrder: sortField === 'role' ? sortOrder : null,
      render: (role) => (
        <Tag color={getRoleColor(role)} className="capitalize">
          {role || 'user'}
        </Tag>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      sorter: true,
      sortOrder: sortField === 'is_active' ? sortOrder : null,
      render: (isActive, record) => (
        <div className="flex items-center space-x-2">
          <Tag color={getStatusColor(isActive)}>
            {isActive !== false ? 'Active' : 'Inactive'}
          </Tag>
          {isActive === false && record.id !== user?.id && (
            <Button
              size="small"
              type="link"
              className="text-green-600 hover:text-green-700 p-0 h-auto"
              onClick={() => handleReactivateUser(record)}
              title="Click to reactivate this user account"
            >
              Reactivate
            </Button>
          )}
        </div>
      ),
    },
    {
      title: 'Articles',
      dataIndex: 'articles_count',
      key: 'articles_count',
      sorter: true,
      sortOrder: sortField === 'articles_count' ? sortOrder : null,
      render: (count) => count || 0,
    },
    {
      title: 'Total Views',
      dataIndex: 'total_views',
      key: 'total_views',
      sorter: true,
      sortOrder: sortField === 'total_views' ? sortOrder : null,
      render: (views) => formatNumber(views || 0),
    },
    {
      title: 'Joined',
      dataIndex: 'created_at',
      key: 'created_at',
      sorter: true,
      sortOrder: sortField === 'created_at' ? sortOrder : null,
      render: (date) => date ? new Date(date).toLocaleDateString() : '-',
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 200,
      render: (_, record) => (
        <div className="flex space-x-2">
          <Button
            size="small"
            type="primary"
            onClick={() => handleEditUser(record)}
            icon={<CogIcon className="w-4 h-4" />}
          >
            Edit
          </Button>
          
          {/* Show Reactivate button for inactive users */}
          {record.is_active === false && record.id !== user?.id && (
            <Button
              size="small"
              type="default"
              className="text-green-600 border-green-600 hover:border-green-700 hover:text-green-700"
              onClick={() => handleReactivateUser(record)}
            >
              Reactivate
            </Button>
          )}
          
          {/* Show Delete button for active users */}
          {record.is_active !== false && record.id !== user?.id && (
            <Button
              size="small"
              type="primary"
              danger
              onClick={() => handleDeleteUser(record)}
              icon={<ExclamationTriangleIcon className="w-4 h-4" />}
            >
              Delete
            </Button>
          )}
        </div>
      ),
    },
  ];

  if (loading && users.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  // Calculate statistics from pagination info (since we don't have all users loaded)
  const totalUsers = pagination.total;
  const activeUsers = users.filter(u => u.is_active !== false).length; // Count from current page
  const adminUsers = users.filter(u => u.role === 'admin').length; // Count from current page  
  const writerUsers = users.filter(u => u.role === 'writer').length; // Count from current page

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 lg:py-12">
        {/* Header */}
        <motion.div 
          className="text-center mb-8 sm:mb-12"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent mb-4">
            Admin Dashboard
          </h1>
          <p className="text-lg sm:text-xl text-gray-600 max-w-2xl mx-auto px-4">
            Manage users, roles, and system administration
          </p>
        </motion.div>

        {/* User Management Section */}
        <motion.div 
          className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <div className="bg-gradient-to-r from-indigo-50 to-purple-50 px-4 sm:px-6 lg:px-8 py-4 sm:py-6 border-b border-gray-200">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div>
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center">
                  <div className="w-6 h-6 sm:w-8 sm:h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mr-3">
                    <UserSolid className="w-3 h-3 sm:w-4 sm:h-4 text-white" />
                  </div>
                  User Management
                </h2>
                <p className="text-gray-600 mt-2 text-sm sm:text-base">
                  View and manage all users in the system
                </p>
              </div>
              <Button 
                type="primary" 
                icon={<ArrowPathIcon className="w-4 h-4" />}
                onClick={() => fetchUsers(pagination.current, pagination.pageSize)}
                loading={loading || pagination.loading}
                size={isMobile ? "small" : "default"}
              >
                Refresh
              </Button>
            </div>
          </div>
          
          <div className="p-4 sm:p-6 lg:p-8">
            {/* Search and Filter Controls */}
            <div className="mb-6 bg-gray-50 p-4 rounded-lg">
              {/* Mobile Filter Toggle */}
              {isMobile && (
                <div className="mb-4">
                  <Button
                    type="default"
                    icon={<Bars3Icon className="w-4 h-4" />}
                    onClick={() => setFilterDrawerVisible(true)}
                    className="w-full"
                  >
                    Show Filters & Search
                  </Button>
                </div>
              )}
              
              {/* Desktop Filters */}
              {!isMobile && (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    {/* Search */}
                    <div className="md:col-span-2">
                      <Search
                        placeholder="Search by name or email..."
                        allowClear
                        value={searchText}
                        onChange={(e) => handleSearch(e.target.value)}
                        onSearch={handleSearch}
                        prefix={<MagnifyingGlassIcon className="w-4 h-4 text-gray-400" />}
                        className="w-full"
                      />
                    </div>
                    
                    {/* Role Filter */}
                    <div>
                      <Select
                        value={roleFilter}
                        onChange={handleRoleFilterChange}
                        className="w-full"
                        placeholder="Filter by role"
                      >
                        <Option value="all">All Roles</Option>
                        <Option value="admin">Admin</Option>
                        <Option value="writer">Writer</Option>
                        <Option value="user">User</Option>
                      </Select>
                    </div>
                    
                    {/* Status Filter */}
                    <div>
                      <Select
                        value={statusFilter}
                        onChange={handleStatusFilterChange}
                        className="w-full"
                        placeholder="Filter by status"
                      >
                        <Option value="all">All Status</Option>
                        <Option value="active">Active</Option>
                        <Option value="inactive">Inactive</Option>
                      </Select>
                    </div>
                  </div>
                  
                  {/* Filter Summary and Clear */}
                  <div className="flex justify-between items-center mt-4">
                    <div className="text-sm text-gray-600">
                      Showing <span className="font-semibold">{filteredUsers.length}</span> users on this page
                      <span className="ml-2">
                        (Page {pagination.current} of {Math.ceil(pagination.total / pagination.pageSize)})
                      </span>
                      <span className="ml-2">
                        • Total: <span className="font-semibold">{pagination.total}</span> users
                      </span>
                      {searchText && (
                        <span className="ml-2">
                          • Search: "<span className="font-medium">{searchText}</span>"
                        </span>
                      )}
                      {roleFilter !== 'all' && (
                        <span className="ml-2">
                          • Role: <span className="font-medium capitalize">{roleFilter}</span>
                        </span>
                      )}
                      {statusFilter !== 'all' && (
                        <span className="ml-2">
                          • Status: <span className="font-medium capitalize">{statusFilter}</span>
                        </span>
                      )}
                    </div>
                    
                    {(searchText || roleFilter !== 'all' || statusFilter !== 'all') && (
                      <Button 
                        type="link" 
                        onClick={clearFilters}
                        icon={<FunnelIcon className="w-4 h-4" />}
                      >
                        Clear Filters
                      </Button>
                    )}
                  </div>
                </>
              )}
              
              {/* Mobile Filter Summary */}
              {isMobile && (
                <div className="text-sm text-gray-600 text-center">
                  Showing <span className="font-semibold">{filteredUsers.length}</span> users on this page
                  <span className="block mt-1">
                    Page {pagination.current} of {Math.ceil(pagination.total / pagination.pageSize)} • Total: {pagination.total}
                  </span>
                  {(searchText || roleFilter !== 'all' || statusFilter !== 'all') && (
                    <span className="block mt-1">
                      Filters applied • <Button 
                        type="link" 
                        onClick={clearFilters}
                        size="small"
                        className="p-0 h-auto text-blue-600"
                      >
                        Clear All
                      </Button>
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Mobile User Cards */}
            {isMobile && (
              <div className="space-y-4">
                {filteredUsers.map((userRecord) => (
                  <Card key={userRecord.id} className="shadow-sm border border-gray-200">
                    <div className="space-y-3">
                      {/* User Info */}
                      <div className="flex items-center space-x-3">
                        {userRecord.avatar_url ? (
                          <img 
                            src={userRecord.avatar_url} 
                            alt={userRecord.full_name}
                            className="w-12 h-12 rounded-full object-cover"
                          />
                        ) : (
                          <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center">
                            <UserIcon className="w-6 h-6 text-gray-500" />
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-gray-900 truncate">{userRecord.full_name}</h3>
                          <p className="text-sm text-gray-500 truncate">{userRecord.email}</p>
                        </div>
                      </div>
                      
                      {/* Tags */}
                      <div className="flex flex-wrap gap-2">
                        <Tag color={getRoleColor(userRecord.role)} className="capitalize">
                          {userRecord.role || 'user'}
                        </Tag>
                        <Tag color={getStatusColor(userRecord.is_active)}>
                          {userRecord.is_active !== false ? 'Active' : 'Inactive'}
                        </Tag>
                      </div>
                      
                      {/* Stats */}
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div className="text-center">
                          <div className="font-semibold text-gray-900">{userRecord.articles_count || 0}</div>
                          <div className="text-gray-500">Articles</div>
                        </div>
                        <div className="text-center">
                          <div className="font-semibold text-gray-900">{formatNumber(userRecord.total_views || 0)}</div>
                          <div className="text-gray-500">Views</div>
                        </div>
                        <div className="text-center">
                          <div className="font-semibold text-gray-900">
                            {userRecord.created_at ? new Date(userRecord.created_at).toLocaleDateString() : '-'}
                          </div>
                          <div className="text-gray-500">Joined</div>
                        </div>
                      </div>
                      
                      {/* Actions */}
                      <div className="flex gap-2 pt-2 border-t border-gray-100">
                        <Button
                          size="small"
                          type="primary"
                          onClick={() => handleEditUser(userRecord)}
                          icon={<CogIcon className="w-4 h-4" />}
                          className="flex-1"
                        >
                          Edit
                        </Button>
                        
                        {userRecord.is_active === false && userRecord.id !== user?.id && (
                          <Button
                            size="small"
                            type="default"
                            className="text-green-600 border-green-600 hover:border-green-700 hover:text-green-700 flex-1"
                            onClick={() => handleReactivateUser(userRecord)}
                          >
                            Reactivate
                          </Button>
                        )}
                        
                        {userRecord.is_active !== false && userRecord.id !== user?.id && (
                          <Button
                            size="small"
                            type="primary"
                            danger
                            onClick={() => handleDeleteUser(userRecord)}
                            icon={<ExclamationTriangleIcon className="w-4 h-4" />}
                            className="flex-1"
                          >
                            Delete
                          </Button>
                        )}
                      </div>
                    </div>
                  </Card>
                ))}
                
                {/* Mobile Pagination */}
                <div className="flex justify-center mt-6">
                  <div className="flex space-x-2">
                    <Button
                      size="small"
                      disabled={pagination.current === 1}
                      loading={pagination.loading}
                      onClick={() => fetchUsers(pagination.current - 1, pagination.pageSize)}
                    >
                      Previous
                    </Button>
                    <span className="px-3 py-2 text-sm text-gray-600">
                      Page {pagination.current} of {Math.ceil(pagination.total / pagination.pageSize)}
                    </span>
                    <Button
                      size="small"
                      disabled={pagination.current >= Math.ceil(pagination.total / pagination.pageSize)}
                      loading={pagination.loading}
                      onClick={() => fetchUsers(pagination.current + 1, pagination.pageSize)}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* Desktop Table */}
            {!isMobile && (
              <Table
                columns={getDesktopColumns()}
                dataSource={filteredUsers}
                rowKey="id"
                loading={loading || pagination.loading}
                scroll={{ x: 1200 }}
                pagination={{
                  current: pagination.current,
                  pageSize: pagination.pageSize,
                  total: pagination.total, // Use total from backend
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total, range) => 
                    `${range[0]}-${range[1]} of ${total} users`,
                  pageSizeOptions: ['10', '20', '50', '100'],
                  onShowSizeChange: (current, size) => {
                    fetchUsers(1, size); // Fetch new page size from backend
                  },
                  responsive: true,
                  position: ['bottomRight']
                }}
                onChange={handleTableChange}
              />
            )}
          </div>
        </motion.div>

        {/* Edit User Modal */}
        <Modal
          title={`Edit User: ${selectedUser?.full_name}`}
          open={editModalVisible}
          onOk={handleUpdateUser}
          onCancel={() => setEditModalVisible(false)}
          confirmLoading={updating}
          okText="Update User"
          width={isMobile ? '90%' : 520}
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Role
              </label>
              <Select
                value={editForm.role}
                onChange={(value) => setEditForm(prev => ({ ...prev, role: value }))}
                className="w-full"
              >
                <Option value="user">User</Option>
                <Option value="writer">Writer</Option>
                <Option value="admin">Admin</Option>
              </Select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Status
              </label>
              <Select
                value={editForm.is_active}
                onChange={(value) => setEditForm(prev => ({ ...prev, is_active: value }))}
                className="w-full"
              >
                <Option value={true}>Active</Option>
                <Option value={false}>Inactive</Option>
              </Select>
              <p className="text-xs text-gray-500 mt-1">
                Set to "Active" to reactivate deactivated accounts, or "Inactive" to deactivate accounts
              </p>
            </div>

            {selectedUser?.id === user?.id && editForm.is_active === false && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-center">
                  <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600 mr-2" />
                  <span className="text-sm text-yellow-800">
                    Warning: You cannot deactivate your own account.
                  </span>
                </div>
              </div>
            )}
            
            {selectedUser?.is_active === false && editForm.is_active === true && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center">
                  <div className="w-5 h-5 bg-green-600 rounded-full flex items-center justify-center mr-2">
                    <span className="white text-xs">✓</span>
                  </div>
                  <span className="text-sm text-green-800">
                    This will reactivate the user account. The user will be able to log in and access the system again.
                  </span>
                </div>
              </div>
            )}
          </div>
        </Modal>

        {/* Delete User Confirmation Modal */}
        <Modal
          title="Delete User"
          open={deleteModalVisible}
          onOk={confirmDeleteUser}
          onCancel={() => {
            setDeleteModalVisible(false);
            setSelectedUser(null);
          }}
          confirmLoading={deleting}
          okText="Delete User"
          okType="danger"
          cancelText="Cancel"
          width={isMobile ? '90%' : 520}
        >
          <div className="space-y-4">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center">
                <ExclamationTriangleIcon className="w-5 h-5 text-red-600 mr-2" />
                <span className="text-sm text-red-800 font-medium">
                  Warning: This action cannot be undone!
                </span>
              </div>
            </div>
            
            <div className="text-gray-700">
              <p>Are you sure you want to delete the user <strong>"{selectedUser?.full_name}"</strong>?</p>
              <p className="mt-2 text-sm text-gray-600">
                This will set the user's status to inactive (soft delete). Their articles will remain in the system.
              </p>
            </div>
          </div>
        </Modal>

        {/* Mobile Filter Drawer */}
        <Drawer
          title="Search & Filters"
          placement="right"
          onClose={() => setFilterDrawerVisible(false)}
          open={filterDrawerVisible}
          width={320}
          className="md:hidden"
        >
          <div className="space-y-6">
            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search Users
              </label>
              <Search
                placeholder="Search by name or email..."
                allowClear
                value={searchText}
                onChange={(e) => handleSearch(e.target.value)}
                onSearch={handleSearch}
                prefix={<MagnifyingGlassIcon className="w-4 h-4 text-gray-400" />}
                className="w-full"
              />
            </div>
            
            {/* Role Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Filter by Role
              </label>
              <Select
                value={roleFilter}
                onChange={handleRoleFilterChange}
                className="w-full"
                placeholder="Filter by role"
              >
                <Option value="all">All Roles</Option>
                <Option value="admin">Admin</Option>
                <Option value="writer">Writer</Option>
                <Option value="user">User</Option>
              </Select>
            </div>
            
            {/* Status Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Filter by Status
              </label>
              <Select
                value={statusFilter}
                onChange={handleStatusFilterChange}
                className="w-full"
                placeholder="Filter by status"
              >
                <Option value="all">All Status</Option>
                <Option value="active">Active</Option>
                <Option value="inactive">Inactive</Option>
              </Select>
            </div>
            
            {/* Active Filters Summary */}
            {(searchText || roleFilter !== 'all' || statusFilter !== 'all') && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="text-sm font-medium text-blue-800 mb-2">Active Filters:</h4>
                <div className="space-y-2 text-sm text-blue-700">
                  {searchText && (
                    <div>• Search: "{searchText}"</div>
                  )}
                  {roleFilter !== 'all' && (
                    <div>• Role: {roleFilter}</div>
                  )}
                  {statusFilter !== 'all' && (
                    <div>• Status: {statusFilter}</div>
                  )}
                </div>
              </div>
            )}
            
            {/* Clear Filters Button */}
            {(searchText || roleFilter !== 'all' || statusFilter !== 'all') && (
              <Button 
                type="default" 
                onClick={clearFilters}
                icon={<FunnelIcon className="w-4 h-4" />}
                className="w-full"
              >
                Clear All Filters
              </Button>
            )}
            
            {/* Results Count */}
            <div className="text-center text-sm text-gray-600 pt-4 border-t border-gray-200">
              Showing <span className="font-semibold">{filteredUsers.length}</span> users on this page
              <div className="mt-1">
                Page {pagination.current} of {Math.ceil(pagination.total / pagination.pageSize)} • Total: <span className="font-semibold">{pagination.total}</span> users
              </div>
            </div>
          </div>
        </Drawer>
      </div>
    </div>
  );
};

export default Dashboard;