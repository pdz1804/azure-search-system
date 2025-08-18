# Article Management System - Frontend

Frontend React.js cho hệ thống quản lý bài viết.

## Tính năng

- 🔐 Xác thực người dùng (đăng nhập/đăng ký)
- 📝 Tạo, chỉnh sửa, xóa bài viết
- 🔍 Tìm kiếm bài viết và người dùng
- 👤 Quản lý hồ sơ cá nhân
- ❤️ Thích và theo dõi
- 💬 Bình luận bài viết
- 📱 Responsive design
- 🌐 Hỗ trợ tiếng Việt

## Công nghệ sử dụng

- **React** 18.2.0 - Framework frontend
- **React Router** 6.8.0 - Điều hướng
- **Ant Design** 5.1.0 - UI Component Library
- **Axios** 1.3.0 - HTTP Client
- **React Quill** 2.0.0 - Rich Text Editor

## Cài đặt

1. Cài đặt dependencies:
```bash
npm install
```

2. Tạo file `.env` và cấu hình:
```env
REACT_APP_API_URL=http://localhost:8000
```

3. Chạy ứng dụng:
```bash
npm start
```

Ứng dụng sẽ chạy tại http://localhost:3000

## Cấu trúc thư mục

```
src/
├── api/                 # API configuration và services
│   ├── config.js       # Axios configuration
│   ├── authApi.js      # Authentication API
│   ├── articleApi.js   # Article API
│   └── userApi.js      # User API
├── components/         # Reusable components
│   ├── Header.js       # Navigation header
│   ├── ArticleCard.js  # Article card component
│   ├── ArticleList.js  # Article list component
│   ├── ArticleForm.js  # Article form component
│   └── ProtectedRoute.js # Route protection
├── context/           # React Context
│   └── AuthContext.js # Authentication context
├── pages/             # Page components
│   ├── Home.js        # Trang chủ
│   ├── Login.js       # Đăng nhập
│   ├── Register.js    # Đăng ký
│   ├── ArticleDetail.js # Chi tiết bài viết
│   ├── Profile.js     # Hồ sơ người dùng
│   ├── Search.js      # Tìm kiếm
│   ├── WriteArticle.js # Viết bài
│   └── NotFound.js    # 404 page
├── utils/             # Utility functions
│   └── helpers.js     # Helper functions
├── App.js             # Main App component
├── index.js           # Entry point
└── index.css          # Global styles
```

## Scripts

- `npm start` - Chạy development server
- `npm run build` - Build production
- `npm test` - Chạy tests
- `npm run eject` - Eject từ Create React App

## Environment Variables

```env
REACT_APP_API_URL=http://localhost:8000  # Backend API URL
```

## API Integration

Frontend tích hợp với backend FastAPI thông qua các service:

- **authApi.js** - Xử lý authentication
- **articleApi.js** - CRUD operations cho bài viết
- **userApi.js** - Quản lý người dùng

## Authentication

Sử dụng JWT tokens với:
- Access token lưu trong localStorage
- Automatic token refresh
- Protected routes
- Role-based access control

## UI/UX

- Responsive design cho mobile và desktop
- Ant Design components
- Vietnamese localization
- Loading states và error handling
- Rich text editor cho nội dung bài viết

## Development

1. Đảm bảo backend API đang chạy
2. Cập nhật `REACT_APP_API_URL` trong `.env`
3. Chạy `npm start` để bắt đầu development

## Build & Deploy

```bash
# Build production
npm run build

# Serve static files
npx serve -s build
```

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
