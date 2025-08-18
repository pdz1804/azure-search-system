import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import viVN from 'antd/locale/vi_VN';
import { AuthProvider } from './context/AuthContext';
import Header from './components/Header';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import ArticleDetail from './pages/ArticleDetail';
import Profile from './pages/Profile';
import Search from './pages/Search';
import WriteArticle from './pages/WriteArticle';
import MyArticles from './pages/MyArticles';
import Bookmarks from './pages/Bookmarks';
import Dashboard from './pages/Dashboard';
import NotFound from './pages/NotFound';
import ProtectedRoute from './components/ProtectedRoute';

// Ant Design theme configuration
const theme = {
  token: {
    colorPrimary: '#1890ff',
    borderRadius: 6,
    colorBgContainer: '#ffffff',
  },
  components: {
    Layout: {
      bodyBg: '#f5f5f5',
    },
  },
};

function App() {
  return (
    <ConfigProvider locale={viVN} theme={theme}>
      <AuthProvider>
        <Router>
          <div className="App">
            <Header />
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/articles/:id" element={<ArticleDetail />} />
              <Route path="/search" element={<Search />} />
              <Route path="/profile/:id?" element={<Profile />} />
              
              {/* Protected Routes */}
              <Route 
                path="/write" 
                element={
                  <ProtectedRoute>
                    <WriteArticle />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/write/:id" 
                element={
                  <ProtectedRoute>
                    <WriteArticle />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/my-articles" 
                element={
                  <ProtectedRoute>
                    <MyArticles />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/bookmarks" 
                element={
                  <ProtectedRoute>
                    <Bookmarks />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/dashboard" 
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                } 
              />
              
              <Route path="*" element={<NotFound />} />
            </Routes>
          </div>
        </Router>
      </AuthProvider>
    </ConfigProvider>
  );
}

export default App;
