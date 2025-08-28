import React, { useState, useEffect } from 'react';
import { Layout, Typography, Button, Space, Card, Row, Col, Avatar } from 'antd';
import { EditOutlined, FileTextOutlined, UserOutlined, ArrowRightOutlined, EyeOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { articleApi } from '../api/articleApi';
import { userApi } from '../api/userApi';
import Hero from '../components/Hero';
import CTASection from '../components/CTASection';
import StatsBar from '../components/StatsBar';
import FeatureGrid from '../components/FeatureGrid';

// Redis caching is now handled on the backend - no frontend cache needed

const { Content } = Layout;
const { Title, Paragraph, Text } = Typography;

const Home = () => {
	const navigate = useNavigate();
	const { isAuthenticated, hasRole } = useAuth();
	const [selectedCategory, setSelectedCategory] = useState(null);
	const [statistics, setStatistics] = useState({
		articles: '500+',
		authors: '50+',
		total_views: '10000+',
		bookmarks: 0
	});
	const [categories, setCategories] = useState([]);
	const [featuredAuthors, setFeaturedAuthors] = useState([]);
	const [loading, setLoading] = useState(true);
	const [statsLoading, setStatsLoading] = useState(true);
	const [categoriesLoading, setCategoriesLoading] = useState(true);
	const [authorsLoading, setAuthorsLoading] = useState(true);

	useEffect(() => {
		const fetchData = async () => {
			try {
				setLoading(true);
				
				// Launch all API calls concurrently - Redis caching handled on backend
				const [statsResult, categoriesResult, authorsResult] = await Promise.allSettled([
					articleApi.getStatistics().finally(() => setStatsLoading(false)),
					articleApi.getCategories().finally(() => setCategoriesLoading(false)),
					userApi.getAllUsers(1, 7, true).finally(() => setAuthorsLoading(false)) // Use featured=true to get featured authors
				]);

				// Handle statistics result
				if (statsResult.status === 'fulfilled' && statsResult.value?.success && statsResult.value.data) {
					setStatistics({
						articles: statsResult.value.data.articles ?? statsResult.value.data.total_articles ?? '0',
						authors: statsResult.value.data.authors ?? '0',
						total_views: statsResult.value.data.total_views ?? '0',
						bookmarks: statsResult.value.data.bookmarks ?? 0
					});
				} else if (statsResult.status === 'rejected') {
					console.warn('Failed to load statistics:', statsResult.reason);
				}

				// Handle categories result
				if (categoriesResult.status === 'fulfilled' && categoriesResult.value?.success) {
					const transformedCategories = categoriesResult.value.data.map((cat, index) => {
						const colors = [
							'from-blue-500 to-indigo-600',
							'from-purple-500 to-pink-600',
							'from-emerald-500 to-teal-600',
							'from-orange-500 to-red-600',
							'from-green-500 to-emerald-600',
							'from-yellow-500 to-orange-600'
						];
						return {
							name: cat.name,
							color: colors[index % colors.length]
						};
					});
					console.log('Categories loaded:', transformedCategories.length);
					setCategories(transformedCategories);
				} else if (categoriesResult.status === 'rejected') {
					console.warn('Failed to load categories:', categoriesResult.reason);
				}

				// Handle authors result
				if (authorsResult.status === 'fulfilled' && authorsResult.value?.success) {
					const authorsData = (authorsResult.value.data?.items || authorsResult.value.data || []).slice(0, 7);
					setFeaturedAuthors(authorsData);
					console.log('Authors loaded:', authorsData.length);
					console.log('Featured authors data:', authorsData.map(a => ({
						name: a.full_name || a.name,
						articles: a.articles_count || 0,
						views: a.total_views || 0,
						id: a.id || a.user_id
					})));
					
					// Debug: Check raw data structure
					console.log('Raw featured authors data:', authorsData.slice(0, 3).map(a => ({
						full_name: a.full_name,
						name: a.name,
						articles_count: a.articles_count,
						total_views: a.total_views,
						all_fields: Object.keys(a)
					})));
				} else if (authorsResult.status === 'rejected') {
					console.warn('Failed to load authors:', authorsResult.reason);
				}
			} catch (error) {
				console.error('Error fetching home data:', error);
			} finally {
				setLoading(false);
			}
		};

		fetchData();
	}, []);

	const handleCategoryChange = (category) => {
		setSelectedCategory(category);
		// Navigate to blogs page with category filter
		navigate('/blogs', { state: { category } });
	};

	const handleExploreBlogs = () => {
		navigate('/blogs');
	};

	return (
		<Layout style={{ minHeight: '100vh', background: 'transparent' }}>
			<Content style={{ padding: 0 }}>
				<Hero 
					onPrimaryClick={() => navigate('/write')}
					onSecondaryClick={handleExploreBlogs}
					selectedCategory={selectedCategory}
					onCategoryChange={handleCategoryChange}
					categories={categories}
					loading={categoriesLoading}
				/>
				
				<FeatureGrid />
				
				<StatsBar totals={statistics} loading={statsLoading} />
				
				{/* Featured Authors Section */}
				{featuredAuthors.length > 0 && (
					<section className="mx-auto my-12 sm:my-16 max-w-7xl px-4 sm:px-6">
						<div className="text-center mb-8 sm:mb-12">
							<Title level={2} className="text-2xl sm:text-3xl font-bold text-gray-900 mb-3">
								Featured Authors
							</Title>
							<Paragraph className="text-base sm:text-lg text-gray-600">
								Meet talented authors from our community
							</Paragraph>
						</div>
						<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
							{featuredAuthors.slice(0, 6).map((author) => (
								<Card 
									key={author.id} 
									className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer"
									bodyStyle={{ padding: '16px sm:24px' }}
									onClick={() => navigate(`/profile/${author.id}`)}
								>
									<div className="text-center">
										<Avatar 
											size={{ xs: 64, sm: 80 }} 
											src={author.avatar_url} 
											className="border-4 border-indigo-100 shadow-md mb-3 sm:mb-4"
										>
											{author.full_name?.[0] || <UserOutlined />}
										</Avatar>
										<Title level={4} className="mb-2 text-gray-900 text-base sm:text-lg">
											{author.full_name || 'Unknown Author'}
										</Title>
										{author.bio && (
											<Paragraph className="text-gray-600 text-xs sm:text-sm mb-3 line-clamp-2">
												{author.bio}
											</Paragraph>
										)}
										<div className="flex justify-center gap-3 sm:gap-4 text-xs sm:text-sm text-gray-500">
											<span><FileTextOutlined className="mr-1" />{(author.articles_count || 0).toLocaleString()}</span>
											<span><EyeOutlined className="mr-1" />{(author.total_views || 0).toLocaleString()}</span>
										</div>
									</div>
								</Card>
							))}
						</div>
					</section>
				)}
				
				{/* Enhanced CTA Section */}
				<section className="relative mx-auto my-12 sm:my-16 max-w-7xl overflow-hidden rounded-2xl sm:rounded-3xl bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 px-4 sm:px-8 py-12 sm:py-16 text-white">
					<div className="absolute -left-10 -top-10 h-40 w-40 rounded-full bg-white/20 blur-2xl" />
					<div className="absolute -right-10 -bottom-10 h-40 w-40 rounded-full bg-white/10 blur-2xl" />
					<div className="relative text-center">
						<h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-3 sm:mb-4">Ready to explore amazing content?</h2>
						<p className="text-base sm:text-lg lg:text-xl text-white/90 mb-6 sm:mb-8 max-w-2xl mx-auto px-2">
							Visit our blogs section to discover featured articles, browse all content, and meet talented authors from our community.
						</p>
						<div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center items-center">
							<Button 
								size="large"
								className="bg-white text-indigo-700 border-0 px-6 sm:px-8 py-2 sm:py-3 h-10 sm:h-12 text-base sm:text-lg font-semibold rounded-full hover:bg-gray-50 hover:scale-105 transition-all duration-300 shadow-lg w-full sm:w-auto"
								onClick={handleExploreBlogs}
							>
								<FileTextOutlined className="mr-2" />
								Explore Blogs
								<ArrowRightOutlined className="ml-2" />
							</Button>
							{isAuthenticated() && (hasRole('writer') || hasRole('admin')) && (
								<Button 
									type="default"
									size="large"
									className="bg-transparent text-white border-2 border-white px-6 sm:px-8 py-2 sm:py-3 h-10 sm:h-12 text-base sm:text-lg font-semibold rounded-full hover:bg-white hover:text-indigo-700 transition-all duration-300 w-full sm:w-auto"
									onClick={() => navigate('/write')}
								>
									<EditOutlined className="mr-2" />
									Start Writing
								</Button>
							)}
						</div>
					</div>
				</section>

				<CTASection />
			</Content>
		</Layout>
	);
};

export default Home;
