import React, { useState, useEffect } from 'react';
import { Form, Input, Button, Upload, Select, message, Card, Switch } from 'antd';
import { UploadOutlined, SaveOutlined } from '@ant-design/icons';
import ReactQuill from 'react-quill';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import 'react-quill/dist/quill.snow.css';
import { articleApi } from '../api/articleApi';
import { useNavigate, useParams } from 'react-router-dom';

const { TextArea } = Input;
const { Option } = Select;

const ArticleForm = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [content, setContent] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const [useMarkdown, setUseMarkdown] = useState(false);
  const [isEdit, setIsEdit] = useState(false);
  const navigate = useNavigate();
  const { id } = useParams();

  useEffect(() => {
    if (id) {
      setIsEdit(true);
      fetchArticle();
    }
  }, [id]);

  const fetchArticle = async () => {
    try {
      const res = await articleApi.getArticle(id);
      const article = res.success ? res.data : res;
      form.setFieldsValue({
        title: article.title,
        abstract: article.abstract,
        tags: article.tags,
        status: article.status,
      });
      setContent(article.content);
    } catch (error) {
      message.error('Failed to load article information');
      navigate('/');
    }
  };

  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      const articleData = {
        ...values,
        content,
        image: imageFile
      };

      if (isEdit) {
        await articleApi.updateArticle(id, articleData);
        message.success('Article updated successfully');
      } else {
        await articleApi.createArticle(articleData);
        message.success('Article created successfully');
      }
      
      navigate('/');
    } catch (error) {
      message.error(isEdit ? 'Failed to update article' : 'Failed to create article');
    } finally {
      setLoading(false);
    }
  };

  const handleImageChange = (info) => {
    if (info.file.status === 'done' || info.file.originFileObj) {
      const file = info.file.originFileObj || info.file;
      setImageFile(file);
      
      // Preview the image
      if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          // You can add image preview here if needed
          console.log('Image loaded:', file.name, file.size);
        };
        reader.readAsDataURL(file);
      }
    }
  };

  const uploadProps = {
    name: 'image',
    listType: 'picture',
    maxCount: 1,
    beforeUpload: () => false, // Prevent auto upload
    onChange: handleImageChange,
    accept: 'image/*',
    showUploadList: {
      showPreviewIcon: true,
      showRemoveIcon: true,
      showDownloadIcon: false,
    },
  };

  const modules = {
    toolbar: [
      [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
      ['bold', 'italic', 'underline', 'strike'],
      [{ 'list': 'ordered'}, { 'list': 'bullet' }],
      [{ 'script': 'sub'}, { 'script': 'super' }],
      [{ 'indent': '-1'}, { 'indent': '+1' }],
      [{ 'direction': 'rtl' }],
      [{ 'color': [] }, { 'background': [] }],
      [{ 'align': [] }],
      ['link', 'image', 'video'],
      ['clean']
    ],
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '24px' }}>
      <Card 
        title={isEdit ? 'Edit Article' : 'Create New Article'} 
        style={{ 
          borderRadius: 16,
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
          border: 'none'
        }}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            status: 'published',
            tags: []
          }}
        >
          <Form.Item
            name="title"
            label="Title"
            rules={[{ required: true, message: 'Please enter a title' }]}
          >
            <Input size="large" placeholder="Enter article title..." />
          </Form.Item>

          <Form.Item
            name="abstract"
            label="Abstract"
            rules={[{ required: true, message: 'Please enter an abstract' }]}
          >
            <TextArea 
              rows={3} 
              placeholder="Enter a brief summary of your article..."
            />
          </Form.Item>

          <Form.Item label="Editor Mode">
            <Switch checked={useMarkdown} onChange={setUseMarkdown} />
            <span style={{ marginLeft: 8 }}>{useMarkdown ? 'Markdown' : 'Rich Text'}</span>
          </Form.Item>

          {useMarkdown ? (
            <>
              <Form.Item label="Content (Markdown)" required>
                <Input.TextArea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  rows={12}
                  placeholder="Enter Markdown content..."
                />
              </Form.Item>
              <Card size="small" title="Preview" style={{ marginBottom: 24 }}>
                <div className="prose max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{content || ''}</ReactMarkdown>
                </div>
              </Card>
            </>
          ) : (
            <Form.Item label="Content" required>
              <ReactQuill
                theme="snow"
                value={content}
                onChange={setContent}
                modules={modules}
                style={{ height: 300, marginBottom: 40 }}
                placeholder="Write your article content..."
              />
            </Form.Item>
          )}

          <Form.Item
            name="tags"
            label="Tags"
          >
            <Select
              mode="tags"
              style={{ width: '100%' }}
              placeholder="Enter tags and press Enter"
              tokenSeparators={[',']}
            />
          </Form.Item>

          <Form.Item
            name="status"
            label="Status"
          >
            <Select>
              <Option value="draft">Draft</Option>
              <Option value="published">Published</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="Cover Image"
          >
            <Upload {...uploadProps}>
              <Button icon={<UploadOutlined />}>Choose Image</Button>
            </Upload>
          </Form.Item>

          <Form.Item>
            <Button 
              type="primary" 
              htmlType="submit" 
              loading={loading}
              icon={<SaveOutlined />}
              size="large"
              style={{
                borderRadius: 20,
                height: 48,
                paddingLeft: 32,
                paddingRight: 32,
                fontSize: 16
              }}
            >
              {isEdit ? 'Update Article' : 'Create Article'}
            </Button>
            <Button 
              style={{ 
                marginLeft: 8,
                borderRadius: 20,
                height: 48,
                paddingLeft: 32,
                paddingRight: 32,
                fontSize: 16
              }} 
              onClick={() => navigate('/')}
              size="large"
            >
              Cancel
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default ArticleForm;
