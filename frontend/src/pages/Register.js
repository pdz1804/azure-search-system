import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, message, Upload, Space } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined, UploadOutlined } from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const { Title, Text } = Typography;

const Register = () => {
  const [loading, setLoading] = useState(false);
  const [avatarFile, setAvatarFile] = useState(null);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      const userData = {
        full_name: values.full_name,
        email: values.email,
        password: values.password,
        avatar: avatarFile
      };

      const result = await register(userData);
      if (result.success) {
        message.success('Đăng ký thành công!');
        navigate('/');
      } else {
        message.error(result.error);
      }
    } catch (error) {
      message.error('Đăng ký thất bại');
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarChange = (info) => {
    if (info.file.status === 'done' || info.file.originFileObj) {
      setAvatarFile(info.file.originFileObj || info.file);
    }
  };

  const uploadProps = {
    name: 'avatar',
    listType: 'picture',
    maxCount: 1,
    beforeUpload: () => false,
    onChange: handleAvatarChange,
  };

  return (
    <div style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      background: '#f0f2f5',
      padding: '24px'
    }}>
      <Card style={{ width: 450, boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Title level={2}>Đăng ký</Title>
          <Text type="secondary">Tạo tài khoản mới</Text>
        </div>

        <Form
          name="register"
          onFinish={handleSubmit}
          layout="vertical"
          size="large"
        >
          <Form.Item
            name="full_name"
            label="Họ và tên"
            rules={[
              { required: true, message: 'Vui lòng nhập họ và tên!' },
              { min: 2, message: 'Họ và tên phải có ít nhất 2 ký tự!' }
            ]}
          >
            <Input 
              prefix={<UserOutlined />} 
              placeholder="Nhập họ và tên của bạn"
            />
          </Form.Item>

          <Form.Item
            name="email"
            label="Email"
            rules={[
              { required: true, message: 'Vui lòng nhập email!' },
              { type: 'email', message: 'Email không hợp lệ!' }
            ]}
          >
            <Input 
              prefix={<MailOutlined />} 
              placeholder="Nhập email của bạn"
            />
          </Form.Item>

          <Form.Item
            name="password"
            label="Mật khẩu"
            rules={[
              { required: true, message: 'Vui lòng nhập mật khẩu!' },
              { min: 6, message: 'Mật khẩu phải có ít nhất 6 ký tự!' }
            ]}
          >
            <Input.Password 
              prefix={<LockOutlined />} 
              placeholder="Nhập mật khẩu của bạn"
            />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            label="Xác nhận mật khẩu"
            dependencies={['password']}
            rules={[
              { required: true, message: 'Vui lòng xác nhận mật khẩu!' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('Mật khẩu xác nhận không khớp!'));
                },
              }),
            ]}
          >
            <Input.Password 
              prefix={<LockOutlined />} 
              placeholder="Nhập lại mật khẩu"
            />
          </Form.Item>

          <Form.Item
            label="Ảnh đại diện (tùy chọn)"
          >
            <Upload {...uploadProps}>
              <Button icon={<UploadOutlined />}>Chọn ảnh</Button>
            </Upload>
          </Form.Item>

          <Form.Item>
            <Button 
              type="primary" 
              htmlType="submit" 
              loading={loading}
              block
            >
              Đăng ký
            </Button>
          </Form.Item>

          <div style={{ textAlign: 'center' }}>
            <Space direction="vertical">
              <Text type="secondary">
                Đã có tài khoản? <Link to="/login">Đăng nhập ngay</Link>
              </Text>
            </Space>
          </div>
        </Form>
      </Card>
    </div>
  );
};

export default Register;
