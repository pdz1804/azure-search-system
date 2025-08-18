import React, { useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { 
  Layout, 
  Input, 
  Button, 
  Space, 
  Avatar, 
  Dropdown,
  Badge,
  Typography,
  message
} from 'antd';
import { 
  SearchOutlined, 
  PlusOutlined, 
  UserOutlined, 
  LoginOutlined,
  LogoutOutlined,
  ProfileOutlined,
  FileTextOutlined,
  HeartOutlined,
  DashboardOutlined,
  BookOutlined,
  UserAddOutlined
} from '@ant-design/icons';
import { useAuth } from '../context/AuthContext';

const { Header: AntHeader } = Layout;
const { Search } = Input;
const { Text } = Typography;

const Header = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout, isAuthenticated } = useAuth();
  const [searchValue, setSearchValue] = useState('');

  const handleSearch = (value) => {
    if (value.trim()) {
      navigate(`/search?q=${encodeURIComponent(value.trim())}`);
    }
  };

  const handleLogout = () => {
    logout();
    message.success('Đã đăng xuất');
    navigate('/');
  };

  const getUserMenuItems = () => {
    const baseItems = [
      {
        key: 'profile',
        icon: <ProfileOutlined />,
        label: 'Hồ sơ của tôi',
        onClick: () => navigate('/profile')
      },
      {
        key: 'bookmarks',
        icon: <HeartOutlined />,
        label: 'Bài viết đã lưu',
        onClick: () => navigate('/bookmarks')
      }
    ];

    // Thêm menu cho writer và admin
    if (user?.role === 'writer' || user?.role === 'admin') {
      baseItems.push(
        {
          key: 'my-articles',
          icon: <FileTextOutlined />,
          label: 'Bài viết của tôi',
          onClick: () => navigate('/my-articles')
        },
        {
          key: 'create-article',
          icon: <PlusOutlined />,
          label: 'Viết bài mới',
          onClick: () => navigate('/write')
        }
      );
    }

    // Thêm dashboard cho admin và writer
    if (user?.role === 'admin' || user?.role === 'writer') {
      baseItems.push({
        key: 'dashboard',
        icon: <DashboardOutlined />,
        label: 'Dashboard',
        onClick: () => navigate('/dashboard')
      });
    }

    baseItems.push(
      { type: 'divider' },
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: 'Đăng xuất',
        onClick: handleLogout
      }
    );

    return baseItems;
  };

  return (
    <AntHeader style={{ 
      background: '#fff', 
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      padding: '0 24px',
      position: 'sticky',
      top: 0,
      zIndex: 1000
    }}>
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        maxWidth: 1200,
        margin: '0 auto'
      }}>
        {/* Logo */}
        <Link to="/" style={{ textDecoration: 'none' }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <BookOutlined style={{ fontSize: '24px', color: '#1890ff', marginRight: '8px' }} />
            <Text strong style={{ fontSize: '20px', color: '#1890ff' }}>
              ArticleHub
            </Text>
          </div>
        </Link>

        {/* Search */}
        <div style={{ flex: 1, maxWidth: 400, margin: '0 24px' }}>
          <Search
            placeholder="Tìm kiếm bài viết..."
            allowClear
            enterButton={<SearchOutlined />}
            size="middle"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            onSearch={handleSearch}
          />
        </div>

        {/* Right Menu */}
        <Space size="middle">
          {isAuthenticated() ? (
            <>
              {/* Create Article Button for writers/admins */}
              {(user?.role === 'writer' || user?.role === 'admin') && (
                <Button 
                  type="primary" 
                  icon={<PlusOutlined />}
                  onClick={() => navigate('/write')}
                >
                  Viết bài
                </Button>
              )}

              {/* User Menu */}
              <Dropdown
                menu={{ items: getUserMenuItems() }}
                placement="bottomRight"
                trigger={['click']}
              >
                <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
                  <Avatar 
                    src={user?.avatar_url}
                    icon={<UserOutlined />}
                    style={{ marginRight: '8px' }}
                  />
                  <Space>
                    <Text strong>{user?.full_name}</Text>
                    {user?.role === 'admin' && (
                      <Badge color="red" text="Admin" />
                    )}
                    {user?.role === 'writer' && (
                      <Badge color="blue" text="Writer" />
                    )}
                  </Space>
                </div>
              </Dropdown>
            </>
          ) : (
            <Space>
              <Button 
                type="default"
                icon={<LoginOutlined />}
                onClick={() => navigate('/login', { state: { from: location } })}
              >
                Đăng nhập
              </Button>
              <Button 
                type="primary"
                icon={<UserAddOutlined />}
                onClick={() => navigate('/register')}
              >
                Đăng ký
              </Button>
            </Space>
          )}
        </Space>
      </div>
    </AntHeader>
  );
};

export default Header;
