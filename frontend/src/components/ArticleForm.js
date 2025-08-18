import React, { useState, useEffect } from 'react';
import { Form, Input, Button, Upload, Select, message, Card, Switch } from 'antd';
import { UploadOutlined, SaveOutlined } from '@ant-design/icons';
import ReactQuill from 'react-quill';
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
      const article = await articleApi.getArticle(id);
      form.setFieldsValue({
        title: article.title,
        abstract: article.abstract,
        tags: article.tags,
        status: article.status,
      });
      setContent(article.content);
    } catch (error) {
      message.error('Không thể tải thông tin bài viết');
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
        message.success('Cập nhật bài viết thành công');
      } else {
        await articleApi.createArticle(articleData);
        message.success('Tạo bài viết thành công');
      }
      
      navigate('/');
    } catch (error) {
      message.error(isEdit ? 'Không thể cập nhật bài viết' : 'Không thể tạo bài viết');
    } finally {
      setLoading(false);
    }
  };

  const handleImageChange = (info) => {
    if (info.file.status === 'done' || info.file.originFileObj) {
      setImageFile(info.file.originFileObj || info.file);
    }
  };

  const uploadProps = {
    name: 'image',
    listType: 'picture',
    maxCount: 1,
    beforeUpload: () => false, // Prevent auto upload
    onChange: handleImageChange,
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
      <Card title={isEdit ? 'Chỉnh sửa bài viết' : 'Tạo bài viết mới'}>
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
            label="Tiêu đề"
            rules={[{ required: true, message: 'Vui lòng nhập tiêu đề' }]}
          >
            <Input size="large" placeholder="Nhập tiêu đề bài viết..." />
          </Form.Item>

          <Form.Item
            name="abstract"
            label="Tóm tắt"
            rules={[{ required: true, message: 'Vui lòng nhập tóm tắt' }]}
          >
            <TextArea 
              rows={3} 
              placeholder="Nhập tóm tắt ngắn gọn về bài viết..."
            />
          </Form.Item>

          <Form.Item
            label="Nội dung"
            required
          >
            <ReactQuill
              theme="snow"
              value={content}
              onChange={setContent}
              modules={modules}
              style={{ height: 300, marginBottom: 40 }}
              placeholder="Viết nội dung bài viết của bạn..."
            />
          </Form.Item>

          <Form.Item
            name="tags"
            label="Thẻ (Tags)"
          >
            <Select
              mode="tags"
              style={{ width: '100%' }}
              placeholder="Nhập các thẻ và nhấn Enter"
              tokenSeparators={[',']}
            />
          </Form.Item>

          <Form.Item
            name="status"
            label="Trạng thái"
          >
            <Select>
              <Option value="draft">Bản nháp</Option>
              <Option value="published">Xuất bản</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="Ảnh đại diện"
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
              icon={<SaveOutlined />}
              size="large"
            >
              {isEdit ? 'Cập nhật' : 'Tạo bài viết'}
            </Button>
            <Button 
              style={{ marginLeft: 8 }} 
              onClick={() => navigate('/')}
              size="large"
            >
              Hủy
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default ArticleForm;
