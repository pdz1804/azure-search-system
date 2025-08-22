import React, { useState, useEffect } from 'react';
import { Layout, Typography, Tabs, Card, Avatar, Spin, Button, Tag, Space, Row, Col, Pagination, Input, Select } from 'antd';
import { 
	FileTextOutlined, 
	UserOutlined, 
	EyeOutlined, 
	HeartOutlined, 
	BookOutlined,
	ClockCircleOutlined,
	MessageOutlined,
	EditOutlined,
	DeleteOutlined
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ArticleList from '../components/ArticleList';
import { userApi } from '../api/userApi';
import { articleApi } from '../api/articleApi';
import { formatNumber, formatDate } from '../utils/helpers';

const { Content } = Layout;
const { Title, Paragraph, Text } = Typography;
const { TabPane } = Tabs;
const { Search } = Input;
const { Option } = Select;

const Blogs = () => {
	const navigate = useNavigate();
	const location = useLocation();
	const { isAuthenticated, hasRole, user } = useAuth();

	// Read params
	const params = new URLSearchParams(location.search);
	const qCategory = params.get('category') || 'all';
	const qSort = params.get('sort') || 'updated_at';
	const qSearch = params.get('search') || '';
	const qPage = parseInt(params.get('page') || '1', 10);
	const qTab = params.get('tab') || 'articles';
	const qAuthorPage = parseInt(params.get('apage') || '1', 10);

	const [activeTab, setActiveTab] = useState(qTab);
	const [authors, setAuthors] = useState([]);
	const [authorsLoading, setAuthorsLoading] = useState(false);
	const [categories, setCategories] = useState([]);
	const [selectedCategory, setSelectedCategory] = useState(qCategory);
	const [articleSearch, setArticleSearch] = useState(qSearch);
	const [articleSortBy, setArticleSortBy] = useState(qSort);
	const [articlePage, setArticlePage] = useState(qPage);
	const [authorPage, setAuthorPage] = useState(qAuthorPage);
	const authorPageSize = 10;

	// Sync URL on changes
	useEffect(() => {
		const next = new URLSearchParams();
		next.set('tab', activeTab);
		next.set('category', selectedCategory || 'all');
		next.set('sort', articleSortBy || 'updated_at');
		if (articleSearch) next.set('search', articleSearch); else next.delete('search');
		next.set('page', String(articlePage || 1));
		next.set('apage', String(authorPage || 1));
		navigate({ pathname: '/blogs', search: `?${next.toString()}` }, { replace: true });
	}, [activeTab, selectedCategory, articleSortBy, articleSearch, articlePage, authorPage]);

	// Load categories (top 10) from backend with graceful fallback
	useEffect(() => {
		const loadCategories = async () => {
			try {
				const res = await articleApi.getCategories();
				if (res && res.success) {
					const items = Array.isArray(res.data) ? res.data : [];
					const top = [...items]
						.sort((a, b) => (b.count || 0) - (a.count || 0))
						.slice(0, 10)
						.map(c => ({ key: c.name, label: c.name, color: 'blue' }));
					setCategories([{ key: 'all', label: 'All', color: 'blue' }, ...top]);
				} else {
					setCategories([{ key: 'all', label: 'All', color: 'blue' }]);
				}
			} catch (e) {
				setCategories([{ key: 'all', label: 'All', color: 'blue' }]);
			}
		};
		loadCategories();
	}, []);

	// Load top authors list
	const loadAuthors = async () => {
		setAuthorsLoading(true);
		try {
			const response = await userApi.getAllUsers(1, 100);
			if (response.success) {
				const items = response.data?.items || response.data || [];
				const sorted = [...items].sort((a, b) => (b.followers || 0) - (a.followers || 0)).slice(0, 100);
				setAuthors(sorted);
			}
		} catch (error) {
			console.error('Failed to load authors:', error);
		} finally {
			setAuthorsLoading(false);
		}
	};

	useEffect(() => { loadAuthors(); }, []);

	// Initialize category from Home navigation state if provided
	useEffect(() => {
		const initialCategory = location?.state?.category;
		if (initialCategory) {
			setSelectedCategory(initialCategory);
			setArticlePage(1);
		}
	}, [location?.state?.category]);

	const handleTabChange = (key) => { setActiveTab(key); };

	const renderAuthorCard = (author) => (
		<Card key={author.id} className="mb-6 border-0 shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer" bodyStyle={{ padding: '24px' }} onClick={() => navigate(`/profile/${author.id}`)}>
			<Row align="middle" gutter={24}>
				<Col>
					<Avatar size={80} src={author.avatar_url} className="border-4 border-indigo-100 shadow-md">{author.full_name?.[0] || <UserOutlined />}</Avatar>
				</Col>
				<Col flex="auto">
					<Space direction="vertical" size="small" style={{ width: '100%' }}>
						<Title level={3} className="mb-2 text-surface cursor-pointer hover:link-accent transition-colors">{author.full_name || 'Unknown Author'}</Title>
						<Text type="secondary" className="block mb-3 text-base">{author.email}</Text>
					</Space>
				</Col>
				<Col>
					<Button type="primary" size="large" className="rounded-full px-8 py-2 h-12 text-base font-medium shadow-lg hover:shadow-xl transition-all duration-300" onClick={(e) => { e.stopPropagation(); navigate(`/profile/${author.id}`); }}>View Profile</Button>
				</Col>
			</Row>
		</Card>
	);

	return (
		<Layout className="min-h-screen" style={{ background: 'var(--bg)' }}>
			<Content className="py-8">
				<div className="max-w-7xl mx-auto px-6">
					<div className="text-center mb-12">
						<Title level={1} className="text-5xl font-extrabold text-surface mb-4"><span className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">Blogs & Articles</span></Title>
						<Paragraph className="text-xl text-muted max-w-3xl mx-auto">Discover amazing content from our community of writers and creators</Paragraph>
					</div>

					<Tabs activeKey={activeTab} onChange={handleTabChange} size="large" className="bg-surface rounded-2xl shadow-xl p-6 border-surface" tabBarStyle={{ marginBottom: 24 }} items={[
						{
							key: 'articles',
							label: (<span className="text-lg font-medium"><FileTextOutlined className="mr-2" />News Articles</span>),
							children: (
								<div>
									<div className="mb-6 flex flex-wrap gap-3 items-center justify-between">
										<div className="flex flex-wrap gap-3">
											{categories.map((category) => (
												<Button key={category.key} type={selectedCategory === category.key ? 'primary' : 'default'} className={`rounded-full px-6 py-2 h-10 font-medium transition-all duration-300 ${selectedCategory === category.key ? 'bg-gradient-to-r from-indigo-600 to-purple-600 border-0 shadow-lg' : 'hover:shadow-md'}`} onClick={() => { setSelectedCategory(category.key); setArticlePage(1); }}>
													{category.label}
												</Button>
											))}
										</div>
										<div className="flex items-center gap-3">
											<Select value={articleSortBy} onChange={(v) => { setArticleSortBy(v); setArticlePage(1); }} style={{ width: 180 }}>
												<Option value="updated_at">Sort by: Updated</Option>
												<Option value="created_at">Sort by: Created</Option>
											</Select>
											<Search placeholder="Search articles..." allowClear enterButton defaultValue={articleSearch} onSearch={(v) => { setArticleSearch(v); setArticlePage(1); }} style={{ maxWidth: 320 }} />
										</div>
									</div>
									<ArticleList showFilters={false} category={selectedCategory} sortBy={articleSortBy} searchQuery={articleSearch} currentPage={articlePage} onPageChange={setArticlePage} showTopPager loadAll />
								</div>
							)
						},
						{
							key: 'authors',
							label: (<span className="text-lg font-medium"><UserOutlined className="mr-2" />Hot Authors</span>),
							children: (
								<div>
									<div className="mb-6 flex justify-end">
										<Search placeholder="Search authors..." allowClear enterButton onSearch={async (val) => { if (!val) { loadAuthors(); return; } try { const res = await userApi.searchUsersAI({ q: val, limit: 100, page: 1 }); const list = res.results || res.data || []; setAuthors(list); setAuthorPage(1); } catch {} }} style={{ maxWidth: 320 }} />
									</div>
									{authorsLoading ? (
										<div className="text-center py-16"><Spin size="large" /></div>
									) : authors.length > 0 ? (
										<div>
											{authors
												.slice()
												.sort((a,b) => (a.full_name||'').localeCompare(b.full_name||''))
												.slice((authorPage - 1) * authorPageSize, authorPage * authorPageSize)
												.map(renderAuthorCard)}
											<div className="mt-6 flex justify-center">
												<Pagination current={authorPage} pageSize={authorPageSize} total={authors.length} showSizeChanger={false} onChange={setAuthorPage} />
											</div>
										</div>
									) : (
										<div className="text-center py-16"><UserOutlined className="text-6xl text-muted mb-4" /><Title level={3} className="text-muted mb-2">No Authors Found</Title><Text className="text-muted">We're working on bringing you amazing authors soon!</Text></div>
									)}
								</div>
							)
						}
					]} />
				</div>
			</Content>
		</Layout>
	);
};

export default Blogs;
