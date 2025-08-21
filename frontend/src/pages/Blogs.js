import React, { useState, useEffect } from 'react';
import { Layout, Typography, Tabs, Card, Avatar, Spin, Button, Tag, Space, Row, Col } from 'antd';
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
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ArticleList from '../components/ArticleList';
import { userApi } from '../api/userApi';
import { formatNumber, formatDate } from '../utils/helpers';

const { Content } = Layout;
const { Title, Paragraph, Text } = Typography;
const { TabPane } = Tabs;

const Blogs = () => {
	const navigate = useNavigate();
	const { isAuthenticated, hasRole, user } = useAuth();
	const [activeTab, setActiveTab] = useState('featured');
	const [authors, setAuthors] = useState([]);
	const [authorsLoading, setAuthorsLoading] = useState(false);
	const [selectedCategory, setSelectedCategory] = useState('all');

	const categories = [
		{ key: 'all', label: 'All Categories', color: 'blue' },
		{ key: 'technology', label: 'Technology', color: 'geekblue' },
		{ key: 'design', label: 'Design', color: 'purple' },
		{ key: 'business', label: 'Business', color: 'green' },
		{ key: 'science', label: 'Science', color: 'orange' },
		{ key: 'health', label: 'Health', color: 'cyan' },
		{ key: 'lifestyle', label: 'Lifestyle', color: 'magenta' },
	];

	// Load popular authors for the Authors tab
	const loadAuthors = async () => {
		setAuthorsLoading(true);
		try {
			console.log('Loading featured users...');
			const response = await userApi.getFeaturedUsers(20);
			console.log('Featured users response:', response);
			
			if (response.success) {
				console.log('Setting authors:', response.data);
				setAuthors(response.data || []);
			} else {
				console.log('Featured users failed, trying fallback...');
				// Fallback to search users if featured users fails
				const fallbackResponse = await userApi.searchUsers({ q: '', page: 1, limit: 20 });
				console.log('Fallback response:', fallbackResponse);
				if (fallbackResponse.success) {
					setAuthors(fallbackResponse.data || []);
				}
			}
		} catch (error) {
			console.error('Failed to load authors:', error);
		} finally {
			setAuthorsLoading(false);
		}
	};

	// Load authors when component mounts
	useEffect(() => {
		console.log('Blogs component mounted, loading authors...');
		loadAuthors();
	}, []);
	
	// Debug: Log when authors state changes
	useEffect(() => {
		console.log('Authors state changed:', authors);
		console.log('Authors length:', authors.length);
	}, [authors]);

	const handleTabChange = (key) => {
		setActiveTab(key);
	};

	const renderAuthorCard = (author) => (
		<Card 
			key={author.id} 
			className="mb-6 border-0 shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer"
			bodyStyle={{ padding: '24px' }}
			onClick={() => navigate(`/profile/${author.id}`)}
		>
			<Row align="middle" gutter={24}>
				<Col>
					<Avatar 
						size={80} 
						src={author.avatar_url} 
						className="border-4 border-indigo-100 shadow-md"
					>
						{author.full_name?.[0] || <UserOutlined />}
					</Avatar>
				</Col>
				<Col flex="auto">
					<Space direction="vertical" size="small" style={{ width: '100%' }}>
						<Title level={3} className="mb-2 text-gray-900 cursor-pointer hover:text-indigo-600 transition-colors">
							{author.full_name || 'Unknown Author'}
						</Title>
						<Text type="secondary" className="block mb-3 text-base">
							{author.email}
						</Text>
						{author.bio && (
							<Paragraph className="mb-0 text-gray-600 text-base leading-relaxed">
								{author.bio}
							</Paragraph>
						)}
						<div className="flex items-center gap-4 mt-4">
							<Text className="text-sm text-gray-500">
								<FileTextOutlined className="mr-1" />
								{author.articles_count || 0} articles
							</Text>
							<Text className="text-sm text-gray-500">
								<EyeOutlined className="mr-1" />
								{formatNumber(author.total_views || 0)} views
							</Text>
							<Text className="text-sm text-gray-500">
								<HeartOutlined className="mr-1" />
								{formatNumber(author.total_likes || 0)} likes
							</Text>
						</div>
					</Space>
				</Col>
				<Col>
					<Button 
						type="primary" 
						size="large"
						className="rounded-full px-8 py-2 h-12 text-base font-medium shadow-lg hover:shadow-xl transition-all duration-300"
						onClick={(e) => {
							e.stopPropagation();
							navigate(`/profile/${author.id}`);
						}}
					>
						View Profile
					</Button>
				</Col>
			</Row>
		</Card>
	);

	const renderArticleCard = (article) => (
		<Card 
			key={article.id} 
			className="mb-6 border-0 shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer"
			bodyStyle={{ padding: '24px' }}
			onClick={() => navigate(`/articles/${article.id}`)}
		>
			<Row gutter={24}>
				{article.image && (
					<Col xs={24} sm={8} md={6}>
						<div className="relative overflow-hidden rounded-xl h-48 sm:h-32">
							<img
								src={article.image}
								alt={article.title}
								className="w-full h-full object-cover transition-transform duration-500 hover:scale-110"
							/>
							{article.tags && article.tags.length > 0 && (
								<div className="absolute top-2 left-2">
									<Tag color="blue" className="text-xs font-medium">
										{article.tags[0]}
									</Tag>
								</div>
							)}
						</div>
					</Col>
				)}
				<Col xs={24} sm={article.image ? 16 : 24} md={article.image ? 18 : 24}>
					<div className="h-full flex flex-col justify-between">
						<div>
							<Title level={4} className="mb-3 text-gray-900 cursor-pointer hover:text-indigo-600 transition-colors line-clamp-2">
								{article.title}
							</Title>
							{article.abstract && (
								<Paragraph className="mb-4 text-gray-600 leading-relaxed line-clamp-3">
									{article.abstract}
								</Paragraph>
							)}
							{article.tags && article.tags.length > 0 && (
								<div className="mb-4 flex flex-wrap gap-2">
									{article.tags.slice(0, 3).map((tag, index) => (
										<Tag 
											key={index} 
											color={categories.find(c => c.key === tag.toLowerCase())?.color || 'blue'}
											className="text-xs font-medium px-3 py-1"
										>
											{tag}
										</Tag>
									))}
								</div>
							)}
						</div>
						
						<div className="flex items-center justify-between">
							<div className="flex items-center gap-4 text-sm text-gray-500">
								<Avatar size={32} src={article.author_avatar} className="border-2 border-indigo-100">
									{article.author_name?.[0] || <UserOutlined />}
								</Avatar>
								<span className="font-medium text-gray-700">{article.author_name}</span>
								<span>•</span>
								<ClockCircleOutlined className="mr-1" />
								{formatDate(article.created_at)}
							</div>
							
							<div className="flex items-center gap-4 text-sm text-gray-500">
								<span><EyeOutlined className="mr-1" />{formatNumber(article.views || 0)}</span>
								<span><HeartOutlined className="mr-1" />{formatNumber(article.likes || 0)}</span>
								<span><MessageOutlined className="mr-1" />{formatNumber(article.comments || 0)}</span>
							</div>
						</div>
					</div>
				</Col>
			</Row>
			
			{/* Action buttons - only show if user is authenticated and can edit */}
			{isAuthenticated() && (hasRole('admin') || article.author_id === user?.id) && (
				<div className="mt-4 pt-4 border-t border-gray-100 flex justify-end gap-2">
					<Button 
						type="text" 
						icon={<EditOutlined />}
						className="text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50"
						onClick={(e) => {
							e.stopPropagation();
							navigate(`/write/${article.id}`);
						}}
					>
						Edit
					</Button>
					<Button 
						type="text" 
						danger
						icon={<DeleteOutlined />}
						className="hover:bg-red-50"
						onClick={(e) => {
							e.stopPropagation();
							// Handle delete with confirmation
						}}
					>
						Delete
					</Button>
				</div>
			)}
		</Card>
	);

	return (
		<Layout className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
			<Content className="py-8">
				<div className="max-w-7xl mx-auto px-6">
					{/* Page Header */}
					<div className="text-center mb-12">
						<Title level={1} className="text-5xl font-extrabold text-gray-900 mb-4">
							<span className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
								Blogs & Articles
							</span>
						</Title>
						<Paragraph className="text-xl text-gray-600 max-w-3xl mx-auto">
							Discover amazing content from our community of writers and creators
						</Paragraph>
					</div>

					{/* Category Filter */}
					<div className="mb-8 text-center">
						<div className="flex flex-wrap justify-center gap-3">
							{categories.map((category) => (
								<Button
									key={category.key}
									type={selectedCategory === category.key ? 'primary' : 'default'}
									className={`rounded-full px-6 py-2 h-10 font-medium transition-all duration-300 ${
										selectedCategory === category.key 
											? 'bg-gradient-to-r from-indigo-600 to-purple-600 border-0 shadow-lg' 
											: 'hover:shadow-md'
									}`}
									onClick={() => setSelectedCategory(category.key)}
								>
									{category.label}
								</Button>
							))}
						</div>
					</div>

					{/* Main Content Tabs */}
					<Tabs 
						activeKey={activeTab} 
						onChange={handleTabChange} 
						size="large"
						className="bg-white rounded-2xl shadow-xl p-6"
						tabBarStyle={{ marginBottom: 24 }}
						items={[
							{
								key: 'featured',
								label: (
									<span className="text-lg font-medium">
										<FileTextOutlined className="mr-2" />
										Featured Articles
									</span>
								),
								children: (
									<div>
										<div className="mb-8">
											<Title level={2} className="text-3xl font-bold text-gray-900 mb-3">
												Featured Articles
											</Title>
											<Paragraph className="text-lg text-gray-600">
												Discover the most popular and engaging articles from our community
											</Paragraph>
										</div>
										<ArticleList showFilters={false} category={selectedCategory} />
									</div>
								)
							},
							{
								key: 'all',
								label: (
									<span className="text-lg font-medium">
										<FileTextOutlined className="mr-2" />
										All Articles
									</span>
								),
								children: (
									<div>
										<div className="mb-8">
											<Title level={2} className="text-3xl font-bold text-gray-900 mb-3">
												All Articles
											</Title>
											<Paragraph className="text-lg text-gray-600">
												Explore all articles in our system with advanced filtering options
											</Paragraph>
										</div>
										<ArticleList showFilters={true} category={selectedCategory} />
									</div>
								)
							},
							{
								key: 'authors',
								label: (
									<span className="text-lg font-medium">
										<UserOutlined className="mr-2" />
										Featured Authors
									</span>
								),
								children: (
									<div>
										<div className="mb-8">
											<Title level={2} className="text-3xl font-bold text-gray-900 mb-3">
												Featured Authors
											</Title>
											<Paragraph className="text-lg text-gray-600">
												Meet talented authors from our community
											</Paragraph>
										</div>
										
										{authorsLoading ? (
											<div className="text-center py-16">
												<Spin size="large" />
											</div>
										) : authors.length > 0 ? (
											<div>
												{authors.map(renderAuthorCard)}
											</div>
										) : (
											<div className="text-center py-16">
												<UserOutlined className="text-6xl text-gray-300 mb-4" />
												<Title level={3} className="text-gray-500 mb-2">No Authors Found</Title>
												<Text className="text-gray-400">We're working on bringing you amazing authors soon!</Text>
											</div>
										)}
									</div>
								)
							}
						]}
					/>
				</div>
			</Content>
		</Layout>
	);
};

export default Blogs;
