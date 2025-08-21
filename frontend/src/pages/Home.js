import React, { useState, useEffect } from 'react';
import { Layout, Typography, Button, Space, Card, Row, Col, Avatar } from 'antd';
import { EditOutlined, FileTextOutlined, UserOutlined, ArrowRightOutlined, EyeOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { articleApi } from '../api/articleApi';
import { userApi } from '../api/userApi';
import Hero from '../components/Hero';
import FeatureGrid from '../components/FeatureGrid';
import CTASection from '../components/CTASection';
import StatsBar from '../components/StatsBar';

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

	useEffect(() => {
		const fetchData = async () => {
			try {
				setLoading(true);
				
				// Use static homepage stats per requirements
				
				// Fetch categories (no counts shown)
				const categoriesResponse = await articleApi.getCategories();
				console.log('Categories response:', categoriesResponse);
				if (categoriesResponse.success) {
					// Transform categories to include colors for the Hero component
					const transformedCategories = categoriesResponse.data.map((cat, index) => {
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
					console.log('Transformed categories:', transformedCategories);
					setCategories(transformedCategories);
				}
				
				// Load authors list using allowed endpoint
				const authorsResponse = await userApi.getAllUsers(1, 7);
				if (authorsResponse.success) {
					setFeaturedAuthors((authorsResponse.data?.items || authorsResponse.data || []).slice(0, 7));
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
				/>
				
				<FeatureGrid />
				
				<StatsBar totals={statistics} />
				
				{/* Featured Authors Section */}
				{featuredAuthors.length > 0 && (
					<section className="mx-auto my-16 max-w-7xl px-6">
						<div className="text-center mb-12">
							<Title level={2} className="text-3xl font-bold text-gray-900 mb-3">
								Featured Authors
							</Title>
							<Paragraph className="text-lg text-gray-600">
								Meet talented authors from our community
							</Paragraph>
						</div>
						<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
							{featuredAuthors.slice(0, 6).map((author) => (
								<Card 
									key={author.id} 
									className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer"
									bodyStyle={{ padding: '24px' }}
									onClick={() => navigate(`/profile/${author.id}`)}
								>
									<div className="text-center">
										<Avatar 
											size={80} 
											src={author.avatar_url} 
											className="border-4 border-indigo-100 shadow-md mb-4"
										>
											{author.full_name?.[0] || <UserOutlined />}
										</Avatar>
										<Title level={4} className="mb-2 text-gray-900">
											{author.full_name || 'Unknown Author'}
										</Title>
										{author.bio && (
											<Paragraph className="text-gray-600 text-sm mb-3 line-clamp-2">
												{author.bio}
											</Paragraph>
										)}
										<div className="flex justify-center gap-4 text-sm text-gray-500">
											<span><FileTextOutlined className="mr-1" />{author.articles_count || 0}</span>
											<span><EyeOutlined className="mr-1" />{author.total_views || 0}</span>
										</div>
									</div>
								</Card>
							))}
						</div>
					</section>
				)}
				
				{/* Enhanced CTA Section */}
				<section className="relative mx-auto my-16 max-w-7xl overflow-hidden rounded-3xl bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 px-8 py-16 text-white">
					<div className="absolute -left-10 -top-10 h-40 w-40 rounded-full bg-white/20 blur-2xl" />
					<div className="absolute -right-10 -bottom-10 h-40 w-40 rounded-full bg-white/10 blur-2xl" />
					<div className="relative text-center">
						<h2 className="text-4xl font-bold mb-4">Ready to explore amazing content?</h2>
						<p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
							Visit our blogs section to discover featured articles, browse all content, and meet talented authors from our community.
						</p>
						<div className="flex flex-col sm:flex-row gap-4 justify-center">
							<Button 
								size="large"
								className="bg-white text-indigo-700 border-0 px-8 py-3 h-12 text-lg font-semibold rounded-full hover:bg-gray-50 hover:scale-105 transition-all duration-300 shadow-lg"
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
									className="bg-transparent text-white border-2 border-white px-8 py-3 h-12 text-lg font-semibold rounded-full hover:bg-white hover:text-indigo-700 transition-all duration-300"
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
