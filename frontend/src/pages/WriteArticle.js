import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { 
  Layout, 
  Card, 
  Typography, 
  Button, 
  Space,
  message,
  Spin,
  Modal
} from 'antd';
import { 
  SaveOutlined, 
  EyeOutlined,
  ArrowLeftOutlined,
  FileAddOutlined
} from '@ant-design/icons';
import ArticleForm from '../components/ArticleForm';
import { articleApi } from '../api/articleApi';
import { useAuth } from '../context/AuthContext';

const { Content } = Layout;
const { Title } = Typography;

const WriteArticle = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const { isAuthenticated, user } = useAuth();
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const isEditMode = !!id;

  console.log('WriteArticle component loaded - user:', user, 'isAuthenticated:', isAuthenticated(), 'editMode:', isEditMode);

  useEffect(() => {
    if (!isAuthenticated()) {
      message.warning('Please login to write articles');
      navigate('/login');
      return;
    }

    if (isEditMode) {
      fetchArticle();
    }

    // Warn user before leaving with unsaved changes
    const handleBeforeUnload = (e) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [id, isAuthenticated, hasUnsavedChanges]);

  const fetchArticle = async () => {
    setLoading(true);
    try {
      const data = await articleApi.getArticle(id);
      setArticle(data);
    } catch (error) {
      message.error('Cannot load article');
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (articleData, isDraft = true) => {
    setSaving(true);
    try {
      let savedArticle;
      
      if (isEditMode) {
        savedArticle = await articleApi.updateArticle(id, {
          ...articleData,
          status: isDraft ? 'draft' : 'published'
        });
        message.success(isDraft ? 'Draft saved' : 'Article updated');
      } else {
        savedArticle = await articleApi.createArticle({
          ...articleData,
          status: isDraft ? 'draft' : 'published'
        });
        message.success(isDraft ? 'Draft saved' : 'Article created');
      }

      setHasUnsavedChanges(false);
      
      if (!isDraft) {
        navigate(`/articles/${savedArticle.id}`);
      } else if (!isEditMode) {
        navigate(`/write/${savedArticle.id}`);
      }
    } catch (error) {
      message.error('Không thể lưu bài viết');
    } finally {
      setSaving(false);
    }
  };

  const handlePublish = (articleData) => {
    Modal.confirm({
      title: 'Xuất bản bài viết',
      content: 'Bạn có chắc chắn muốn xuất bản bài viết này?',
      onOk: () => handleSave(articleData, false),
    });
  };

  const handlePreview = (articleData) => {
    // Store article data for preview
    sessionStorage.setItem('preview_article', JSON.stringify(articleData));
    window.open('/preview', '_blank');
  };

  const handleBack = () => {
    if (hasUnsavedChanges) {
      Modal.confirm({
        title: 'Bạn có thay đổi chưa lưu',
        content: 'Bạn có chắc chắn muốn rời khỏi trang mà không lưu?',
        onOk: () => navigate(-1),
      });
    } else {
      navigate(-1);
    }
  };

  const handleFormChange = () => {
    setHasUnsavedChanges(true);
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
          <Card>
            <div style={{ marginBottom: 24 }}>
              <Space>
                <Button 
                  icon={<ArrowLeftOutlined />} 
                  onClick={handleBack}
                >
                  Back
                </Button>
                <Title level={2} style={{ margin: 0 }}>
                  <FileAddOutlined style={{ marginRight: 8 }} />
                  {isEditMode ? 'Modify the Article' : 'Write an Article'}
                </Title>
              </Space>
            </div>

            <ArticleForm
              initialData={article}
              onSave={(data) => handleSave(data, true)}
              onPublish={handlePublish}
              onPreview={handlePreview}
              onChange={handleFormChange}
              loading={saving}
              actions={
                <Space>
                  <Button 
                    icon={<EyeOutlined />}
                    onClick={(form) => {
                      form.validateFields().then(values => {
                        handlePreview(values);
                      });
                    }}
                  >
                    Xem trước
                  </Button>
                  <Button 
                    icon={<SaveOutlined />}
                    loading={saving}
                    onClick={(form) => {
                      form.validateFields().then(values => {
                        handleSave(values, true);
                      });
                    }}
                  >
                    Lưu nháp
                  </Button>
                  <Button 
                    type="primary"
                    loading={saving}
                    onClick={(form) => {
                      form.validateFields().then(values => {
                        handlePublish(values);
                      });
                    }}
                  >
                    Xuất bản
                  </Button>
                </Space>
              }
            />
          </Card>
        </div>
      </Content>
    </Layout>
  );
};

export default WriteArticle;
