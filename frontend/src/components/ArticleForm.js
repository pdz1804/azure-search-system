import React, { useState, useEffect, useRef } from 'react';
import { Form, Input, Button, Upload, Select, message, Card, Switch, Tag, Space, Tooltip, Modal } from 'antd';
import { UploadOutlined, SaveOutlined, BulbOutlined, LoadingOutlined } from '@ant-design/icons';
import ReactQuill, { Quill } from 'react-quill';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import 'react-quill/dist/quill.snow.css';
import { articleApi } from '../api/articleApi';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import { apiClientFormData, createFormData, apiClient } from '../api/config';
import { APP_ID } from '../config/appConfig';

const { TextArea } = Input;
const { Option } = Select;



const ArticleForm = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [content, setContent] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const [useMarkdown, setUseMarkdown] = useState(false);
  const [isEdit, setIsEdit] = useState(false);
  const [suggestedTags, setSuggestedTags] = useState([]);
  const [generatingTags, setGeneratingTags] = useState(false);
  const quillRef = useRef(null);
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

  const generateTags = async () => {
    const title = form.getFieldValue('title');
    const abstract = form.getFieldValue('abstract');
    
    if (!title || !abstract) {
      message.warning('Please enter both title and abstract before generating tags');
      return;
    }

    setGeneratingTags(true);
    try {
      // Backend expects form data, not JSON
      const formData = new FormData();
      formData.append('title', title);
      formData.append('abstract', abstract);
      formData.append('content', content || '');
      formData.append('user_tags', JSON.stringify([])); // No user tags for now
      
      const response = await apiClientFormData.post('/articles/generate-tags', formData);
      
      const tags = response.data?.tags || [];
      setSuggestedTags(tags);
      message.success(`Generated ${tags.length} suggested tags`);
    } catch (error) {
      console.error('Tag generation error:', error);
      message.error('Failed to generate tags. Please try again.');
    } finally {
      setGeneratingTags(false);
    }
  };

  const addSuggestedTag = (tag) => {
    const currentTags = form.getFieldValue('tags') || [];
    if (!currentTags.includes(tag)) {
      form.setFieldsValue({ tags: [...currentTags, tag] });
    }
    // Remove from suggested tags after adding
    setSuggestedTags(prev => prev.filter(t => t !== tag));
  };

  

  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      let processedContent = content;

      // If content contains base64 images (data:image/...), upload them and replace with blob URLs
      const uploadBase64 = async (text) => {
        const regex = /<img[^>]+src=["'](data:image\/[a-zA-Z0-9+\-\.]+;base64,[^"']+)["'][^>]*>/g;
        let match;
        let newText = text;
        const uploads = [];
        while ((match = regex.exec(text)) !== null) {
          const dataUrl = match[1];
          if (!dataUrl) continue;
          uploads.push(dataUrl);
        }

        for (const dataUrl of uploads) {
          try {
            // Convert dataURL to Blob
            const res = await fetch(dataUrl);
            const blob = await res.blob();
            const file = new File([blob], 'upload.png', { type: blob.type });

            const fd = new FormData();
            fd.append('file', file);

            // Use shared axios instance so auth headers and baseURL are applied.
            const uploadResp = await apiClientFormData.post('/files/', fd);
            const url = uploadResp.data?.url || uploadResp.data?.data?.url;
            if (url) {
              newText = newText.split(dataUrl).join(url);
            }
          } catch (e) {
            console.error('Failed to upload inline image', e);
          }
        }

        return newText;
      };

      processedContent = await uploadBase64(content);

      // pick cover image: prefer Form value (AntD Upload) then imageFile state
      let coverFile = imageFile;
      if (values && values.image && Array.isArray(values.image) && values.image.length > 0) {
        const item = values.image[0];
        coverFile = item && item.originFileObj ? item.originFileObj : item;
      }

      const articleData = {
        ...values,
        content: processedContent,
        image: coverFile
      };

      // DEBUG: log imageFile and FormData structure before sending
      try {
        // eslint-disable-next-line no-console
        console.log('[DEBUG] Submitting article; imageFile:', imageFile);
        const debugForm = createFormData(articleData);
        for (const pair of debugForm.entries()) {
          const val = pair[1];
          if (val && typeof val === 'object' && (val.name || val.size)) {
            // eslint-disable-next-line no-console
            console.log('[DEBUG] form field:', pair[0], { name: val.name, size: val.size, type: val.type });
          } else {
            // eslint-disable-next-line no-console
            console.log('[DEBUG] form field:', pair[0], val);
          }
        }
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error('[DEBUG] Failed to inspect FormData before submit', e);
      }

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

  // Normalize Upload event to value for Form
  const normFile = (e) => {
    if (Array.isArray(e)) {
      return e;
    }
    return e && e.fileList ? e.fileList : e;
  };

  const modules = {
    toolbar: {
      container: [
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
      ]
    }
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
                  <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>{content || ''}</ReactMarkdown>
                </div>
              </Card>
            </>
          ) : (
            <Form.Item label="Content" required>
              <ReactQuill
                ref={quillRef}
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
            label={
              <Space>
                Tags
                <Tooltip title="Generate AI-powered tags based on your title and abstract">
                  <Button
                    type="text"
                    size="small"
                    icon={generatingTags ? <LoadingOutlined /> : <BulbOutlined />}
                    onClick={generateTags}
                    loading={generatingTags}
                    style={{ 
                      color: '#1890ff',
                      padding: '0 4px',
                      height: 'auto',
                      fontSize: 12
                    }}
                  >
                    Generate Tags
                  </Button>
                </Tooltip>
              </Space>
            }
          >
            <Select
              mode="tags"
              style={{ width: '100%' }}
              placeholder="Enter tags and press Enter"
              tokenSeparators={[',']}
            />
          </Form.Item>

          {suggestedTags.length > 0 && (
            <Card 
              size="small" 
              title="Suggested Tags" 
              style={{ 
                marginBottom: 16,
                borderColor: '#1890ff',
                backgroundColor: '#f0f8ff'
              }}
            >
              <Space size={[8, 8]} wrap>
                {suggestedTags.map((tag, index) => (
                  <Tag
                    key={index}
                    color="blue"
                    style={{ 
                      cursor: 'pointer',
                      borderStyle: 'dashed'
                    }}
                    onClick={() => addSuggestedTag(tag)}
                  >
                    + {tag}
                  </Tag>
                ))}
              </Space>
              <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                Click on a tag to add it to your article
              </div>
            </Card>
          )}

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
            name="image"
            label="Cover Image"
            valuePropName="fileList"
            getValueFromEvent={normFile}
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
