import React, { useState, useEffect } from 'react';
import { 
	DocumentTextIcon, 
	UserIcon, 
	EyeIcon, 
	HeartIcon, 
	BookOpenIcon,
	ClockIcon,
	ChatBubbleLeftIcon,
	PencilIcon,
	TrashIcon,
	FunnelIcon,
	MagnifyingGlassIcon
} from '@heroicons/react/24/outline';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ArticleList from '../components/ArticleList';
import { userApi } from '../api/userApi';
import { articleApi } from '../api/articleApi';
import { formatNumber, formatDate } from '../utils/helpers';

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

	// Sync URL on changes - but avoid triggering unnecessary navigation
	useEffect(() => {
		const currentParams = new URLSearchParams(location.search);
		const next = new URLSearchParams();
		next.set('tab', activeTab);
		next.set('category', selectedCategory || 'all');
		next.set('sort', articleSortBy || 'updated_at');
		if (articleSearch) next.set('search', articleSearch); else next.delete('search');
		next.set('page', String(articlePage || 1));
		next.set('apage', String(authorPage || 1));
		
		// Only navigate if URL actually changed to prevent pagination reset loops
		if (currentParams.toString() !== next.toString()) {
			navigate({ pathname: '/blogs', search: `?${next.toString()}` }, { replace: true });
		}
	}, [activeTab, selectedCategory, articleSortBy, articleSearch, articlePage, authorPage, location.search]);

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
		<div key={author.id} className="mb-6 bg-white rounded-lg shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer p-6" onClick={() => navigate(`/profile/${author.id}`)}>
			<div className="flex items-center space-x-6">
				<div className="relative">
					{author.avatar_url ? (
						<img 
							src={author.avatar_url} 
							alt={author.full_name || 'Author'} 
							className="w-20 h-20 rounded-full border-4 border-indigo-100 shadow-md object-cover" 
						/>
					) : (
						<div className="w-20 h-20 rounded-full border-4 border-indigo-100 shadow-md bg-indigo-100 flex items-center justify-center">
							<UserIcon className="w-8 h-8 text-indigo-600" />
						</div>
					)}
				</div>
				<div className="flex-1">
					<h3 className="text-xl font-semibold text-gray-900 mb-2 cursor-pointer hover:text-indigo-600 transition-colors">{author.full_name || 'Unknown Author'}</h3>
					<p className="text-gray-600 text-base">{author.email}</p>
				</div>
				<div>
					<button 
						type="button" 
						className="bg-indigo-600 text-white px-8 py-3 rounded-full text-base font-medium shadow-lg hover:shadow-xl hover:bg-indigo-700 transition-all duration-300" 
						onClick={(e) => { e.stopPropagation(); navigate(`/profile/${author.id}`); }}
					>
						View Profile
					</button>
				</div>
			</div>
		</div>
	);

	return (
		<div className="min-h-screen bg-gray-50">
			<div className="py-8">
				<div className="max-w-7xl mx-auto px-6">
					<div className="text-center mb-12">
						<h1 className="text-5xl font-extrabold text-gray-900 mb-4">
							<span className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">Blogs & Articles</span>
						</h1>
						<p className="text-xl text-gray-600 max-w-3xl mx-auto">Discover amazing content from our community of writers and creators</p>
					</div>

					{/* Tab Navigation */}
					<div className="bg-white rounded-2xl shadow-xl p-6 mb-8">
						<div className="flex space-x-8 border-b border-gray-200 mb-6">
							<button
								type="button"
								className={`pb-4 px-2 text-lg font-medium transition-colors duration-200 border-b-2 ${
									activeTab === 'articles' 
										? 'text-indigo-600 border-indigo-600' 
										: 'text-gray-500 border-transparent hover:text-gray-700'
								}`}
								onClick={() => handleTabChange('articles')}
							>
								<DocumentTextIcon className="w-5 h-5 inline-block mr-2" />
								News Articles
							</button>
							<button
								type="button"
								className={`pb-4 px-2 text-lg font-medium transition-colors duration-200 border-b-2 ${
									activeTab === 'authors' 
										? 'text-indigo-600 border-indigo-600' 
										: 'text-gray-500 border-transparent hover:text-gray-700'
								}`}
								onClick={() => handleTabChange('authors')}
							>
								<UserIcon className="w-5 h-5 inline-block mr-2" />
								Hot Authors
							</button>
						</div>

						{/* Articles Tab Content */}
						{activeTab === 'articles' && (
							<div>
								<div className="mb-6 flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
									<div className="flex flex-wrap gap-3">
										{categories.map((category) => (
											<button
												key={category.key}
												type="button"
												className={`rounded-full px-6 py-2 font-medium transition-all duration-300 ${
													selectedCategory === category.key 
														? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg' 
														: 'bg-gray-100 text-gray-700 hover:bg-gray-200 hover:shadow-md'
												}`}
												onClick={() => { setSelectedCategory(category.key); setArticlePage(1); }}
											>
												{category.label}
											</button>
										))}
									</div>
									<div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 w-full md:w-auto">
										<select
											value={articleSortBy}
											onChange={(e) => { setArticleSortBy(e.target.value); setArticlePage(1); }}
											className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none bg-white min-w-[180px]"
										>
											<option value="updated_at">Sort by: Updated</option>
											<option value="created_at">Sort by: Created</option>
										</select>
										<div className="relative max-w-xs w-full">
											<input
												type="text"
												placeholder="Search articles..."
												defaultValue={articleSearch}
												onKeyDown={(e) => {
													if (e.key === 'Enter') {
														setArticleSearch(e.target.value);
														setArticlePage(1);
													}
												}}
												className="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
											/>
											<MagnifyingGlassIcon className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
										</div>
									</div>
								</div>
								<ArticleList 
									showFilters={false} 
									category={selectedCategory} 
									sortBy={articleSortBy} 
									searchQuery={articleSearch} 
									currentPage={articlePage} 
									onPageChange={setArticlePage} 
									showTopPager 
								/>
							</div>
						)}

						{/* Authors Tab Content */}
						{activeTab === 'authors' && (
							<div>
								<div className="mb-6 flex justify-end">
									<div className="relative max-w-xs w-full">
										<input
											type="text"
											placeholder="Search authors..."
											onKeyDown={async (e) => {
												if (e.key === 'Enter') {
													const val = e.target.value;
													if (!val) {
														loadAuthors();
														return;
													}
													try {
														const res = await userApi.searchUsersAI({ q: val, limit: 100, page: 1 });
														const list = res.results || res.data || [];
														setAuthors(list);
														setAuthorPage(1);
													} catch {}
												}
											}}
											className="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
										/>
										<MagnifyingGlassIcon className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
									</div>
								</div>
								{authorsLoading ? (
									<div className="text-center py-16">
										<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
									</div>
								) : authors.length > 0 ? (
									<div>
										{authors
											.slice()
											.sort((a,b) => (a.full_name||'').localeCompare(b.full_name||''))
											.slice((authorPage - 1) * authorPageSize, authorPage * authorPageSize)
											.map(renderAuthorCard)}
										<div className="mt-6 flex justify-center">
											{/* Simple pagination */}
											<div className="flex space-x-2">
												{Array.from({ length: Math.ceil(authors.length / authorPageSize) }, (_, i) => i + 1).map(page => (
													<button
														key={page}
														type="button"
														className={`px-4 py-2 rounded-lg font-medium transition-colors ${
															authorPage === page
																? 'bg-indigo-600 text-white'
																: 'bg-gray-100 text-gray-700 hover:bg-gray-200'
														}`}
														onClick={() => setAuthorPage(page)}
													>
														{page}
													</button>
												))}
											</div>
										</div>
									</div>
								) : (
									<div className="text-center py-16">
										<UserIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
										<h3 className="text-xl font-semibold text-gray-600 mb-2">No Authors Found</h3>
										<p className="text-gray-500">We're working on bringing you amazing authors soon!</p>
									</div>
								)}
							</div>
						)}
					</div>
				</div>
			</div>
		</div>
	);
};

export default Blogs;
