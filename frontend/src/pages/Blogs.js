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
		<div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
			{/* Hero Header */}
			<div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-blue-600 text-white relative overflow-hidden">
				<div className="absolute inset-0 bg-black/10"></div>
				<div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
					<div className="text-center">
						<h1 className="text-4xl md:text-6xl font-extrabold mb-4">
							<span className="bg-gradient-to-r from-white to-blue-100 bg-clip-text text-transparent">Blogs & Articles</span>
						</h1>
						<p className="text-lg md:text-xl text-blue-100 max-w-3xl mx-auto leading-relaxed">Discover amazing content from our community of writers and creators</p>
					</div>
				</div>
			</div>

			<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
				{/* Tab Navigation */}
				<div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-2xl p-6 md:p-8 mb-8 border border-white/50">
					<div className="flex flex-col sm:flex-row sm:space-x-8 border-b border-gray-200 mb-6">
						<button
							type="button"
							className={`pb-4 px-3 text-base md:text-lg font-semibold transition-all duration-300 border-b-3 mb-2 sm:mb-0 ${
								activeTab === 'articles' 
									? 'text-indigo-600 border-indigo-600 bg-indigo-50 rounded-t-lg' 
									: 'text-gray-600 border-transparent hover:text-indigo-500 hover:bg-gray-50 rounded-lg'
							}`}
							onClick={() => handleTabChange('articles')}
						>
							<DocumentTextIcon className="w-5 h-5 inline-block mr-2" />
							News Articles
						</button>
						<button
							type="button"
							className={`pb-4 px-3 text-base md:text-lg font-semibold transition-all duration-300 border-b-3 ${
								activeTab === 'authors' 
									? 'text-indigo-600 border-indigo-600 bg-indigo-50 rounded-t-lg' 
									: 'text-gray-600 border-transparent hover:text-indigo-500 hover:bg-gray-50 rounded-lg'
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
							{/* Controls Section */}
							<div className="mb-6 bg-white/80 backdrop-blur-sm rounded-2xl p-4 shadow-sm border border-gray-100">
								{/* Top Row - Search and Sort */}
								<div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between mb-4">
									<div className="relative flex-1 max-w-md">
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
											className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none bg-white shadow-sm text-sm"
										/>
										<MagnifyingGlassIcon className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
									</div>
									<select
										value={articleSortBy}
										onChange={(e) => { setArticleSortBy(e.target.value); setArticlePage(1); }}
										className="px-3 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none bg-white shadow-sm text-sm min-w-[140px]"
									>
										<option value="updated_at">Latest</option>
										<option value="created_at">Newest</option>
									</select>
								</div>
								
								{/* Categories Row */}
								<div className="flex flex-wrap gap-2">
									{categories.map((category) => (
										<button
											key={category.key}
											type="button"
											className={`px-3 py-1.5 text-xs font-medium rounded-full transition-all duration-200 ${
												selectedCategory === category.key 
													? 'bg-indigo-600 text-white shadow-md' 
													: 'bg-gray-100 text-gray-600 hover:bg-indigo-50 hover:text-indigo-600 border border-gray-200'
											}`}
											onClick={() => { setSelectedCategory(category.key); setArticlePage(1); }}
										>
											{category.label}
										</button>
									))}
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
							<div className="mb-6 flex justify-center sm:justify-end">
								<div className="relative max-w-xs w-full sm:w-auto min-w-[280px]">
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
										className="w-full px-4 py-2 pl-10 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none bg-white/90 backdrop-blur-sm shadow-sm"
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
									<div className="mt-8 flex justify-center">
										{/* Enhanced numbered pagination */}
										<div className="flex flex-wrap items-center justify-center gap-2">
											{Array.from({ length: Math.ceil(authors.length / authorPageSize) }, (_, i) => i + 1).map(page => (
												<button
													key={page}
													type="button"
													className={`w-10 h-10 rounded-xl font-semibold transition-all duration-200 ${
														authorPage === page
															? 'bg-indigo-600 text-white shadow-lg scale-110'
															: 'bg-white/70 text-gray-700 hover:bg-white hover:text-indigo-600 hover:shadow-md hover:scale-105 border border-gray-200'
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
	);
};

export default Blogs;
