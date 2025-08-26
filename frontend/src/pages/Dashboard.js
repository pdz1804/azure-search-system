import React, { useState, useEffect } from 'react';
import { message, Table, Button, Modal, Select, Tag, Input, Space } from 'antd';
import { 
  UserIcon,
  CogIcon,
  ExclamationTriangleIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  ArrowPathIcon
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
  const [selectedUser, setSelectedUser] = useState(null);
  const [editForm, setEditForm] = useState({ role: '', is_active: true });
  const [updating, setUpdating] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  });
  
  // Search and filter states
  const [searchText, setSearchText] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortField, setSortField] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('descend');

  useEffect(() => {
    fetchUsers();
  }, []); // Remove pagination dependency since we're fetching all users at once

  // Filter and search users whenever data or filters change
  useEffect(() => {
    applyFilters();
  }, [users, searchText, roleFilter, statusFilter, sortField, sortOrder]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      // For admin dashboard, fetch all users at once with a high limit
      // We'll handle pagination on the frontend for better filtering/searching
      const response = await userApi.getAllUsersAdmin(1, 1000); // Get up to 1000 users
      if (response.success) {
        const allUsers = response.data || [];
        setUsers(allUsers);
        console.log(`Admin Dashboard: Loaded ${allUsers.length} total users`);
      } else {
        message.error('Failed to fetch users');
      }
    } catch (error) {
      message.error('Failed to load users');
      console.error('Error fetching users:', error);
    } finally {
      setLoading(false);
    }
  };

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

      // Handle different data types
      if (sortField === 'created_at') {
        aValue = new Date(aValue || 0).getTime();
        bValue = new Date(bValue || 0).getTime();
      } else if (typeof aValue === 'string') {
        aValue = aValue?.toLowerCase() || '';
        bValue = bValue?.toLowerCase() || '';
      } else if (typeof aValue === 'number') {
        aValue = aValue || 0;
        bValue = bValue || 0;
      }

      if (sortOrder === 'ascend') {
        return aValue > bValue ? 1 : aValue < bValue ? -1 : 0;
      } else {
        return aValue < bValue ? 1 : aValue > bValue ? -1 : 0;
      }
    });

    setFilteredUsers(filtered);
  };

  const handleEditUser = (user) => {
    setSelectedUser(user);
    setEditForm({
      role: user.role || 'user',
      is_active: user.is_active !== false
    });
    setEditModalVisible(true);
  };

  const handleUpdateUser = async () => {
    if (!selectedUser) return;
    
    try {
      setUpdating(true);
      const response = await userApi.updateUser(selectedUser.id, editForm);
      if (response.success) {
        message.success('User updated successfully');
        setEditModalVisible(false);
        setSelectedUser(null);
        fetchUsers(); // Refresh the list
      } else {
        message.error(response.error || 'Failed to update user');
      }
    } catch (error) {
      message.error('Failed to update user');
      console.error('Error updating user:', error);
    } finally {
      setUpdating(false);
    }
  };

  const handleTableChange = (paginationInfo, filters, sorter) => {
    setPagination(prev => ({
      ...prev,
      current: paginationInfo.current
    }));

    // Handle sorting
    if (sorter && sorter.field) {
      setSortField(sorter.field);
      setSortOrder(sorter.order || 'descend');
    }
  };

  const handleSearch = (value) => {
    setSearchText(value);
    // Reset pagination when searching
    setPagination(prev => ({ ...prev, current: 1 }));
  };

  const handleRoleFilterChange = (value) => {
    setRoleFilter(value);
    setPagination(prev => ({ ...prev, current: 1 }));
  };

  const handleStatusFilterChange = (value) => {
    setStatusFilter(value);
    setPagination(prev => ({ ...prev, current: 1 }));
  };

  const clearFilters = () => {
    setSearchText('');
    setRoleFilter('all');
    setStatusFilter('all');
    setSortField('created_at');
    setSortOrder('descend');
    setPagination(prev => ({ ...prev, current: 1 }));
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

  const columns = [
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
          <div>
            <div className="font-medium text-gray-900">{text}</div>
            <div className="text-sm text-gray-500">{record.email}</div>
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
      render: (isActive) => (
        <Tag color={getStatusColor(isActive)}>
          {isActive !== false ? 'Active' : 'Inactive'}
        </Tag>
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50">
      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Header */}
        <motion.div 
          className="text-center mb-12"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h1 className="text-5xl font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent mb-4">
            Admin Dashboard
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
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
          <div className="bg-gradient-to-r from-indigo-50 to-purple-50 px-8 py-6 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mr-3">
                    <UserSolid className="w-4 h-4 text-white" />
                  </div>
                  User Management
                </h2>
                <p className="text-gray-600 mt-2">
                  View and manage all users in the system
                </p>
              </div>
              <Button 
                type="primary" 
                icon={<ArrowPathIcon className="w-4 h-4" />}
                onClick={fetchUsers}
                loading={loading}
              >
                Refresh
              </Button>
            </div>
          </div>
          
          <div className="p-8">
            {/* Search and Filter Controls */}
            <div className="mb-6 bg-gray-50 p-4 rounded-lg">
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
                  Showing <span className="font-semibold">{filteredUsers.length}</span> of <span className="font-semibold">{users.length}</span> users
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
            </div>

            <Table
              columns={columns}
              dataSource={filteredUsers}
              rowKey="id"
              loading={loading}
              pagination={{
                current: pagination.current,
                pageSize: pagination.pageSize,
                total: filteredUsers.length,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => 
                  `${range[0]}-${range[1]} of ${total} users`,
                pageSizeOptions: ['10', '20', '50', '100'],
                onShowSizeChange: (current, size) => {
                  setPagination(prev => ({ ...prev, pageSize: size, current: 1 }));
                }
              }}
              onChange={handleTableChange}
            />
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
          </div>
        </Modal>
      </div>
    </div>
  );
};

export default Dashboard;