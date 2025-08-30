# Frontend - Article Management System

Modern ReactJS frontend application providing a beautiful, responsive interface for article management and AI-powered search capabilities.

## 🚀 Quick Start

### Prerequisites

- Node.js (version 16 or higher)
- npm or yarn
- Backend API running on `http://localhost:8001`

### Installation

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Environment setup:**
   ```bash
   # Create environment file
   echo "REACT_APP_API_BASE_URL=http://localhost:8001" > .env
   echo "REACT_APP_UPLOAD_URL=http://localhost:8001/uploads" >> .env
   ```

4. **Start development server:**
   ```bash
   npm start
   ```

5. **Open application:**
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
frontend/
├── public/
│   ├── index.html                # HTML template
│   └── favicon.ico               # App icon
├── src/
│   ├── App.js                    # Main app component with routing
│   ├── index.js                  # React app entry point
│   ├── index.css                 # Global styles (Tailwind CSS)
│   ├── components/               # Reusable UI components
│   │   ├── ArticleCard.js        # Article display component
│   │   ├── ArticleForm.js        # Article creation/editing form
│   │   ├── ArticleList.js        # Article listing with pagination
│   │   ├── ArticleSkeleton.js    # Loading skeleton for articles
│   │   ├── AuthorCard.js         # Author profile display
│   │   ├── Header.js             # Navigation header with auth
│   │   ├── Footer.js             # Page footer
│   │   ├── Hero.js               # Landing page hero section
│   │   ├── LoadingSpinner.js     # Loading states
│   │   ├── Pagination.js         # Pagination controls
│   │   ├── ProtectedRoute.js     # Route protection wrapper
│   │   ├── ShareModal.js         # Social sharing modal
│   │   └── ConfirmationModal.js  # Action confirmation dialogs
│   ├── pages/                    # Main page components
│   │   ├── Home.js               # Landing/homepage
│   │   ├── Login.js              # User login
│   │   ├── Register.js           # User registration
│   │   ├── Dashboard.js          # User dashboard
│   │   ├── Profile.js            # User profile management
│   │   ├── Blogs.js              # Article browsing
│   │   ├── ArticleDetail.js      # Individual article view
│   │   ├── WriteArticle.js       # Article creation
│   │   ├── MyArticles.js         # User's articles management
│   │   ├── Search.js             # AI-powered search interface
│   │   ├── Bookmarks.js          # Saved articles
│   │   ├── About.js              # About page
│   │   ├── Contact.js            # Contact page
│   │   └── NotFound.js           # 404 error page
│   ├── context/                  # React contexts
│   │   └── AuthContext.js        # Authentication state management
│   ├── api/                      # API service layer
│   │   ├── config.js             # Axios configuration & interceptors
│   │   ├── authApi.js            # Authentication API calls
│   │   ├── articleApi.js         # Article CRUD operations
│   │   └── userApi.js            # User management APIs
│   ├── icons/                    # Custom SVG icon components
│   └── utils/                    # Utility functions and helpers
├── package.json                  # Dependencies and scripts
├── tailwind.config.js            # Tailwind CSS configuration
└── postcss.config.js             # PostCSS configuration
```

## 🎨 Styling

This project uses **Tailwind CSS** for styling with custom configurations:

- Custom color palette
- Animation utilities
- Responsive design utilities
- Typography scale
- Component variants

## ✨ Key Features

### 🔐 Authentication & Authorization
- **JWT-based authentication** with automatic token management
- **Role-based access control** (USER, WRITER, ADMIN)
- **Protected routes** with automatic redirects
- **Profile management** with avatar upload
- **Registration & login** with form validation

### 📝 Article Management
- **Rich text editor** with markdown support
- **Image upload** and media management
- **Draft/publish** workflow
- **Tag system** for categorization
- **Article analytics** (views, likes)
- **Social sharing** to multiple platforms

### 🔍 AI-Powered Search
- **Hybrid search** combining multiple algorithms
- **Real-time search suggestions**
- **Advanced filtering** by tags, authors, dates
- **Search result highlighting**
- **Fuzzy matching** for author names
- **Pagination** for large result sets

### 🎨 User Experience
- **Responsive design** (mobile-first approach)
- **Dark/light theme** support
- **Smooth animations** with Framer Motion
- **Loading states** and skeleton screens
- **Toast notifications** for user feedback
- **Infinite scroll** for article browsing
- **Lazy loading** for images and content

### 📊 Dashboard & Analytics
- **Personal dashboard** with statistics
- **Article management** interface
- **Bookmark system** for saving articles
- **Reading history** and recommendations
- **Author profiles** with article listings

### 👥 Popular Authors & Recommendations
- **Smart author ranking** based on followers, articles, and views
- **Popularity formula**: `(followers × 10,000) + (articles × 100) + views`
- **AI-powered article recommendations** with semantic similarity
- **Fallback system** ensures content availability even when APIs fail
- **Multi-tenant support** with app-specific filtering
- **Real-time caching** for optimal performance

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the frontend directory:

```env
# Backend API Configuration
REACT_APP_API_BASE_URL=http://localhost:8001
REACT_APP_UPLOAD_URL=http://localhost:8001/uploads

# Optional: Enable/disable features
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_NOTIFICATIONS=true

# Social sharing (optional)
REACT_APP_FACEBOOK_APP_ID=your_facebook_app_id
REACT_APP_TWITTER_HANDLE=@your_handle
```

### Tailwind CSS Configuration

Custom theme configuration in `tailwind.config.js`:

```javascript
module.exports = {
  content: ['./src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          900: '#1e3a8a'
        }
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out'
      }
    }
  }
}
```

## 🔌 API Integration

The frontend integrates with the FastAPI backend through dedicated service modules:

### API Services

- **authApi.js** - Authentication and authorization
- **articleApi.js** - Article CRUD operations and management
- **userApi.js** - User profile and management

### HTTP Client Configuration

```javascript
// api/config.js
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL,
  timeout: 10000,
});

// Request interceptor for auth tokens
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### Authentication Flow

1. **Login/Registration** → JWT token storage
2. **Automatic token injection** in API requests
3. **Token validation** on protected routes
4. **Automatic logout** on token expiration
5. **Role-based UI rendering**

## 🎨 Styling Architecture

### Tailwind CSS Approach
- **Utility-first** CSS framework
- **Custom design system** with consistent spacing and colors
- **Responsive breakpoints** for all screen sizes
- **Dark mode support** (future enhancement)

### Component Styling Patterns
```javascript
// Example: Button component with variants
const Button = ({ variant = 'primary', size = 'md', children }) => {
  const baseClasses = 'font-medium rounded-lg transition-colors duration-200';
  const variants = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white',
    secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-900'
  };
  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  };
  
  return (
    <button className={`${baseClasses} ${variants[variant]} ${sizes[size]}`}>
      {children}
    </button>
  );
};
```

## 🔧 Development Workflow

### Prerequisites
1. Ensure backend API is running on `http://localhost:8001`
2. Configure environment variables in `.env`
3. Install dependencies with `npm install`

### Development Commands
```bash
# Start development server
npm start

# Run tests
npm test

# Build for production
npm run build

# Analyze bundle size
npm run analyze
```

### Code Quality
- **ESLint** for code linting
- **Prettier** for code formatting
- **Husky** for git hooks (if configured)
- **Component testing** with React Testing Library

## 🚀 Build & Deployment

### Production Build
```bash
# Create optimized production build
npm run build

# Serve locally for testing
npx serve -s build -p 3000

# Analyze bundle size
npm run analyze
```

### Docker Deployment
```bash
# Build Docker image
docker build -f Dockerfile.frontend -t article-frontend .

# Run container
docker run -p 3000:3000 article-frontend
```

### Environment-Specific Builds
```bash
# Development
REACT_APP_API_BASE_URL=http://localhost:8001 npm run build

# Staging
REACT_APP_API_BASE_URL=https://api-staging.example.com npm run build

# Production
REACT_APP_API_BASE_URL=https://api.example.com npm run build
```

## 🧪 Testing

### Test Structure
```bash
src/
├── components/
│   └── __tests__/
│       ├── ArticleCard.test.js
│       └── Header.test.js
├── pages/
│   └── __tests__/
│       ├── Home.test.js
│       └── Login.test.js
└── utils/
    └── __tests__/
        └── helpers.test.js
```

### Running Tests
```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage

# Run specific test file
npm test ArticleCard.test.js
```

## 📱 Browser Support

| Browser | Minimum Version |
|---------|----------------|
| Chrome  | 90+            |
| Firefox | 88+            |
| Safari  | 14+            |
| Edge    | 90+            |

## 🔄 State Management

### React Context Pattern
```javascript
// context/AuthContext.js
const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const login = async (credentials) => {
    // Login logic
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
```

## 🎯 Performance Optimization

### Code Splitting
- **Route-based splitting** with React.lazy()
- **Component lazy loading** for large components
- **Dynamic imports** for heavy libraries

### Image Optimization
- **Lazy loading** with react-lazy-load-image-component
- **Progressive image loading** with placeholders
- **Responsive images** with multiple sizes

### Bundle Optimization
- **Tree shaking** for unused code elimination
- **Minification** and compression
- **Asset optimization** for faster loading

## 🔮 Future Enhancements

- **Progressive Web App** (PWA) features
- **Offline support** with service workers
- **Push notifications** for new articles
- **Real-time collaboration** for article editing
- **Advanced analytics** and user insights
- **Multi-language support** (i18n)
- **Accessibility improvements** (WCAG 2.1 compliance)
