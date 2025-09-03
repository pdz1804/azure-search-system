import React, { useState, useEffect, useRef } from 'react';
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
import ArticleList, { clearArticleListCache } from '../components/ArticleList';
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
	// Clear article list cache when switching back to articles tab
	useEffect(() => {
	  if (activeTab === 'articles') {
	    clearArticleListCache();
	  }
	}, [activeTab]);

	const [authors, setAuthors] = useState([]);
	const [authorsLoading, setAuthorsLoading] = useState(false);
	const [categories, setCategories] = useState([]);
	const [selectedCategory, setSelectedCategory] = useState(qCategory);
	const [articleSearch, setArticleSearch] = useState(qSearch);
	const [articleSortBy, setArticleSortBy] = useState(qSort);
	const [articlePage, setArticlePage] = useState(qPage);
	const [authorPage, setAuthorPage] = useState(qAuthorPage);
	const [isAuthorSearchMode, setIsAuthorSearchMode] = useState(false);
	const authorPageSize = 10;

	// Refs for search inputs
	const articleSearchRef = useRef(null);
	const authorSearchRef = useRef(null);

	// Helper to normalize followers count regardless of API shape
	const getFollowersCount = (author) => {
		if (!author) return 0;
		const f = author.followers ?? author.followers_count ?? 0;
		if (Array.isArray(f)) return f.length;
		const n = Number(f);
		return Number.isFinite(n) ? n : 0;
	};

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
		setIsAuthorSearchMode(false); // Reset search mode flag
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

	// Enhanced search function that fetches complete user data for search results
	const searchAuthorsWithFullData = async (query) => {
		setAuthorsLoading(true);
		setIsAuthorSearchMode(true); // Set search mode flag
		try {
			// Search for authors using backend search API (returns complete user data)
			const res = await userApi.searchUsersAI({ q: query, limit: 100, page: 1 });
			const searchResults = res.results || res.data || [];
			
			if (searchResults.length === 0) {
				setAuthors([]);
				return;
			}

			// Backend search API already returns complete user data, no need for additional API calls
			setAuthors(searchResults);
			setAuthorPage(1);
		} catch (error) {
			console.error('Failed to search authors:', error);
			setAuthors([]);
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
		<div key={author.id} className="group mb-6 bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 cursor-pointer p-4 sm:p-6 border border-white/50 hover:border-indigo-200" onClick={() => navigate(`/profile/${author.id}`)}>
			<div className="flex flex-col sm:flex-row items-center sm:items-center space-y-4 sm:space-y-0 sm:space-x-6">
				<div className="relative flex-shrink-0">
					{author.avatar_url ? (
						<img 
							src={author.avatar_url} 
							alt={author.full_name || 'Author'} 
							className="w-16 h-16 sm:w-20 sm:h-20 rounded-full border-4 border-indigo-100 shadow-lg object-cover group-hover:border-indigo-200 transition-all duration-300" 
						/>
					) : (
						<div className="w-16 h-16 sm:w-20 sm:h-20 rounded-full border-4 border-indigo-100 shadow-lg bg-gradient-to-br from-indigo-100 to-purple-100 flex items-center justify-center group-hover:border-indigo-200 transition-all duration-300">
							<UserIcon className="w-7 h-7 sm:w-8 sm:h-8 text-indigo-600" />
						</div>
					)}
					<div className="absolute -bottom-1 -right-1 w-6 h-6 bg-green-500 rounded-full border-2 border-white shadow-sm"></div>
				</div>
				<div className="flex-1 text-center sm:text-left min-w-0">
					<h3 className="text-lg sm:text-xl font-bold text-gray-900 mb-1 group-hover:text-indigo-600 transition-colors duration-300 truncate">
						{author.full_name || 'Unknown Author'}
					</h3>
					<p className="text-gray-600 text-sm sm:text-base mb-2 truncate">{author.email}</p>
					<div className="flex flex-wrap justify-center sm:justify-start gap-3 text-xs sm:text-sm text-gray-500">
						<span className="flex items-center gap-1">
							<DocumentTextIcon className="w-3 h-3 sm:w-4 sm:h-4" />
							{author.articles_count || 0} articles
						</span>
						<span className="flex items-center gap-1">
							<EyeIcon className="w-3 h-3 sm:w-4 sm:h-4" />
							{formatNumber(author.total_views || 0)} views
						</span>
						<span className="flex items-center gap-1">
							<HeartIcon className="w-3 h-3 sm:w-4 sm:h-4" />
							{getFollowersCount(author)} followers
						</span>
					</div>
				</div>
				<div className="flex-shrink-0">
					<button 
						type="button" 
						className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-4 sm:px-6 py-2 sm:py-3 rounded-full text-sm sm:text-base font-semibold shadow-lg hover:shadow-xl hover:from-indigo-700 hover:to-purple-700 transition-all duration-300 transform hover:scale-105 group-hover:scale-110" 
						onClick={(e) => { e.stopPropagation(); navigate(`/profile/${author.id}`); }}
					>
						<span className="hidden sm:inline">View Profile</span>
						<span className="sm:hidden">Profile</span>
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
				<div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-2xl p-4 sm:p-6 md:p-8 mb-8 border border-white/50">
					<div className="flex flex-col sm:flex-row gap-2 sm:gap-0 sm:space-x-4 lg:space-x-8 border-b border-gray-200 mb-6">
						<button
							type="button"
							className={`flex items-center justify-center sm:justify-start pt-3 sm:pt-4 pb-3 sm:pb-4 px-4 sm:px-3 text-sm sm:text-base md:text-lg font-semibold transition-all duration-300 border-b-3 rounded-lg sm:rounded-t-lg sm:rounded-b-none ${
								activeTab === 'articles' 
									? 'text-indigo-600 border-indigo-600 bg-indigo-50 shadow-sm' 
									: 'text-gray-600 border-transparent hover:text-indigo-500 hover:bg-gray-50'
							}`}
							onClick={() => handleTabChange('articles')}
						>
							<DocumentTextIcon className="w-4 h-4 sm:w-5 sm:h-5 inline-block mr-2" />
							News Articles
						</button>
						<button
							type="button"
							className={`flex items-center justify-center sm:justify-start pt-3 sm:pt-4 pb-3 sm:pb-4 px-4 sm:px-3 text-sm sm:text-base md:text-lg font-semibold transition-all duration-300 border-b-3 rounded-lg sm:rounded-t-lg sm:rounded-b-none ${
								activeTab === 'authors' 
									? 'text-indigo-600 border-indigo-600 bg-indigo-50 shadow-sm' 
									: 'text-gray-600 border-transparent hover:text-indigo-500 hover:bg-gray-50'
							}`}
							onClick={() => handleTabChange('authors')}
						>
							<UserIcon className="w-4 h-4 sm:w-5 sm:h-5 inline-block mr-2" />
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
											ref={articleSearchRef}
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
										<button
											type="button"
											onClick={() => {
												if (articleSearchRef.current) {
													setArticleSearch(articleSearchRef.current.value);
													setArticlePage(1);
												}
											}}
											className="absolute left-3 top-1/2 transform -translate-y-1/2 hover:text-indigo-600 transition-colors duration-200"
										>
											<MagnifyingGlassIcon className="w-4 h-4 text-gray-400 hover:text-indigo-600" />
										</button>
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
											ref={authorSearchRef}
											type="text"
											placeholder="Search authors..."
											onKeyDown={async (e) => {
												if (e.key === 'Enter') {
													const val = e.target.value;
													if (!val) {
														loadAuthors();
														return;
													}
													await searchAuthorsWithFullData(val);
												}
											}}
											onChange={(e) => {
												// Clear search mode if input is empty
												if (!e.target.value.trim()) {
													setIsAuthorSearchMode(false);
												}
											}}
											className="w-full px-4 py-2 pl-10 pr-20 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none bg-white/90 backdrop-blur-sm shadow-sm"
										/>
										<button
											type="button"
											onClick={async () => {
												if (authorSearchRef.current) {
													const val = authorSearchRef.current.value;
													if (!val) {
														loadAuthors();
														return;
													}
													await searchAuthorsWithFullData(val);
												}
											}}
											className="absolute left-3 top-1/2 transform -translate-y-1/2 hover:text-indigo-600 transition-colors duration-200"
										>
											<MagnifyingGlassIcon className="w-5 h-5 text-gray-400 hover:text-indigo-600" />
										</button>
										{/* Clear search button */}
										{authorSearchRef.current?.value && (
											<button
												type="button"
												onClick={() => {
													if (authorSearchRef.current) {
														authorSearchRef.current.value = '';
														setIsAuthorSearchMode(false);
														loadAuthors();
													}
												}}
												className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-red-500 transition-colors duration-200"
												title="Clear search"
											>
												<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
												</svg>
											</button>
										)}
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
										.sort((a,b) => {
											// If in search mode, preserve the relevance order from the search API
											if (isAuthorSearchMode) {
												return 0; // No sorting, keep search relevance order
											}
											// For default authors list, sort alphabetically by full_name
											return (a.full_name || '').localeCompare(b.full_name || '');
										})
										.slice((authorPage - 1) * authorPageSize, authorPage * authorPageSize)
										.map(renderAuthorCard)}
									<div className="mt-8 flex justify-center">
										{/* Enhanced numbered pagination */}
										<div className="flex flex-wrap items-center justify-center gap-2 p-4 bg-white/50 backdrop-blur-sm rounded-2xl border border-white/60">
											{Array.from({ length: Math.ceil(authors.length / authorPageSize) }, (_, i) => i + 1).map(page => (
												<button
													key={page}
													type="button"
													className={`w-10 h-10 sm:w-12 sm:h-12 rounded-xl font-bold text-sm sm:text-base transition-all duration-200 ${
														authorPage === page
															? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg scale-110 border-2 border-indigo-200'
															: 'bg-white/80 text-gray-700 hover:bg-white hover:text-indigo-600 hover:shadow-md hover:scale-105 border border-gray-200 hover:border-indigo-300'
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
									<div className="bg-white/80 backdrop-blur-sm rounded-3xl p-12 border border-white/60 shadow-lg max-w-md mx-auto">
										<div className="w-20 h-20 bg-gradient-to-br from-gray-100 to-gray-200 rounded-full flex items-center justify-center mx-auto mb-6 shadow-inner">
											<UserIcon className="w-10 h-10 text-gray-400" />
										</div>
										<h3 className="text-2xl font-bold text-gray-700 mb-3">No Authors Found</h3>
										<p className="text-gray-500 leading-relaxed">We're working on bringing you amazing authors soon! Check back later for talented creators from our community.</p>
									</div>
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
