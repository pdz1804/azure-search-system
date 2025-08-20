# Article Management System - Frontend

Modern ReactJS frontend application for article management system.

## 🚀 Quick Start

### Prerequisites
- Node.js (version 16 or higher)
- npm or yarn

### Installation

1. **Clone and navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install all dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm start
   ```

4. **Open your browser:**
   Navigate to `http://localhost:3000`

## 📦 Dependencies

### Main Dependencies
- **React 18** - Core React library
- **React Router DOM** - Navigation and routing
- **Axios** - HTTP client for API calls
- **Framer Motion** - Animation library
- **React Hot Toast** - Toast notifications
- **React Hook Form** - Form handling
- **Date-fns** - Date utilities
- **Heroicons** - Beautiful icons
- **Tailwind CSS** - Utility-first CSS framework
- **React Lazy Load Image** - Image lazy loading
- **React Share** - Social sharing components

### UI/UX Libraries
- **Ant Design** - UI component library (legacy support)
- **React Query** - Server state management
- **React Markdown** - Markdown rendering
- **React Syntax Highlighter** - Code highlighting

### Utilities
- **Lodash** - Utility functions
- **clsx** - Conditional CSS classes
- **use-debounce** - Debouncing hooks

## 🛠️ Available Scripts

- `npm start` - Start development server
- `npm run build` - Build for production
- `npm test` - Run tests
- `npm run analyze` - Analyze bundle size

## 🏗️ Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── ArticleCard.js   # Article display component
│   ├── Header.js        # Navigation header
│   ├── Footer.js        # Page footer
│   ├── LoadingSpinner.js # Loading states
│   └── ...
├── context/             # React contexts
│   └── AuthContext.js   # Authentication context
├── api/                 # API service layer
│   ├── config.js        # Axios configuration
│   ├── authApi.js       # Authentication APIs
│   └── userApi.js       # User-related APIs
├── icons/               # Custom icon components
├── utils/               # Utility functions
└── pages/               # Page components
```

## 🎨 Styling

This project uses **Tailwind CSS** for styling with custom configurations:

- Custom color palette
- Animation utilities
- Responsive design utilities
- Typography scale
- Component variants

## 🚀 Features

- **Modern UI/UX** - Clean, responsive design
- **Authentication** - Complete auth flow
- **Role-based Access** - USER/WRITER/ADMIN roles
- **Article Management** - CRUD operations
- **Social Features** - Likes, shares, bookmarks
- **Real-time Notifications** - Toast and bell notifications
- **Search & Filtering** - Advanced search capabilities
- **Responsive Design** - Mobile-first approach
- **Performance Optimized** - Lazy loading, code splitting

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the frontend directory:

```env
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_UPLOAD_URL=http://localhost:8000/uploads
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
