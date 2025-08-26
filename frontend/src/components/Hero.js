import React, { useEffect, useRef } from 'react';
import { motion, useInView, useAnimation } from 'framer-motion';

const Hero = ({ onPrimaryClick, onSecondaryClick, selectedCategory, onCategoryChange, categories = [], loading = false }) => {
	const ref = useRef(null);
	const isInView = useInView(ref, { once: true });
	const mainControls = useAnimation();
	const categoryControls = useAnimation();

	// Use provided categories or fallback to defaults
	// Ensure all categories have proper colors for visibility
	const defaultColors = [
		'from-blue-500 to-indigo-600',
		'from-purple-500 to-pink-600', 
		'from-emerald-500 to-teal-600',
		'from-orange-500 to-red-600',
		'from-green-500 to-emerald-600',
		'from-yellow-500 to-orange-600',
		'from-rose-500 to-pink-600',
		'from-cyan-500 to-blue-600',
		'from-violet-500 to-purple-600',
		'from-amber-500 to-orange-600'
	];

	const displayCategories = categories.length > 0 
		? categories.map((cat, index) => ({
			...cat,
			// Ensure every category has a color, even if backend doesn't provide one
			color: cat.color || defaultColors[index % defaultColors.length]
		}))
		: [
			{ name: 'Technology', color: 'from-blue-500 to-indigo-600', count: 28 },
			{ name: 'Design', color: 'from-purple-500 to-pink-600', count: 21 },
			{ name: 'Business', color: 'from-emerald-500 to-teal-600', count: 16 },
			{ name: 'Science', color: 'from-orange-500 to-red-600', count: 11 },
			{ name: 'Health', color: 'from-green-500 to-emerald-600', count: 10 },
			{ name: 'Lifestyle', color: 'from-yellow-500 to-orange-600', count: 9 },
		];

	useEffect(() => {
		if (isInView) {
			// start the entrance animations when hero comes into view
			mainControls.start('visible');
			categoryControls.start('visible');
		}
	}, [isInView, mainControls, categoryControls]);

	return (
		<section ref={ref} className="relative overflow-hidden bg-gradient-to-br from-indigo-50 via-white to-purple-50" style={{ background: 'linear-gradient(135deg, rgba(59,130,246,0.03) 0%, var(--bg) 50%, rgba(236,72,153,0.02) 100%)' }}>
			{/* Enhanced background elements */}
			<div className="absolute -top-24 -right-24 w-96 h-96 bg-gradient-to-br from-indigo-200/40 to-purple-200/40 rounded-full blur-3xl animate-pulse" />
			<div className="absolute -bottom-32 -left-32 w-[500px] h-[500px] bg-gradient-to-br from-blue-200/30 to-cyan-200/30 rounded-full blur-3xl animate-pulse delay-1000" />
			<div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-br from-purple-100/20 to-pink-100/20 rounded-full blur-3xl animate-pulse delay-500" />

			<div className="relative mx-auto max-w-7xl px-4 sm:px-6 py-16 sm:py-20 lg:flex lg:items-center lg:gap-16 lg:py-32">
				<motion.div
					className="flex-1"
					variants={{
						hidden: { opacity: 0, x: -50 },
						visible: { opacity: 1, x: 0 }
					}}
					initial="hidden"
					animate={mainControls}
					transition={{ duration: 0.8, ease: 'easeOut' }}
				>
					<motion.p
						className="inline-flex items-center rounded-full px-4 py-2 text-sm font-semibold ring-1 ring-inset shadow-sm"
						style={{ background: 'rgba(255,255,255,0.04)', color: 'var(--muted)', boxShadow: 'none' }}
						initial={{ opacity: 0, y: 8 }}
						animate={{ opacity: 1, y: 0 }}
						transition={{ delay: 0.05, duration: 0.5 }}
					>
						Curated • Insightful • Actionable
					</motion.p>

					<motion.h1
						className="mt-6 text-3xl font-extrabold tracking-tight sm:text-4xl md:text-5xl lg:text-6xl xl:text-7xl"
						initial={{ scale: 0 }}
						animate={{ scale: 1 }}
						transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
					>
						<span className="block bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">Elevate your knowledge</span>
						<span className="block text-indigo-700">with modern brilliance</span>
					</motion.h1>

					<motion.p
						className="mt-6 max-w-3xl text-lg sm:text-xl leading-7 sm:leading-8 text-gray-600"
						initial={{ opacity: 0, y: 20 }}
						animate={{ opacity: 1, y: 0 }}
						transition={{ delay: 0.35, duration: 0.8 }}
					>
						Discover thoughtfully crafted insights from authors worldwide. Write, share, and grow with a fast, elegant interface powered by React and Tailwind CSS.
					</motion.p>

					<motion.div
						className="mt-10 flex flex-col items-center sm:items-start gap-4 sm:flex-row w-full"
						initial={{ opacity: 0, y: 20 }}
						animate={{ opacity: 1, y: 0 }}
						transition={{ delay: 0.5, duration: 0.8 }}
					>
						<button
							onClick={onPrimaryClick}
							className="group relative inline-flex items-center justify-center rounded-full bg-gradient-to-r from-indigo-600 to-purple-600 px-6 sm:px-8 py-3 sm:py-4 text-base sm:text-lg font-semibold text-white shadow-lg transition-all duration-300 hover:shadow-xl hover:scale-105 focus:outline-none focus:ring-4 focus:ring-indigo-300 w-full sm:w-auto"
						>
							<span className="relative z-10">Start Writing</span>
							<div className="absolute inset-0 rounded-full bg-gradient-to-r from-indigo-700 to-purple-700 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
						</button>

						<button
							onClick={onSecondaryClick}
							className="inline-flex items-center justify-center rounded-full px-6 sm:px-8 py-3 sm:py-4 text-base sm:text-lg font-semibold ring-2 ring-inset transition-all duration-300 hover:scale-105 shadow-md w-full sm:w-auto"
							style={{ background: 'var(--card-bg)', color: 'var(--text)', borderColor: 'rgba(255,255,255,0.04)' }}
						>
							Explore Articles
						</button>
					</motion.div>
				</motion.div>

				<motion.div 
					className="mt-16 flex-1 lg:mt-0"
					variants={{
						hidden: { opacity: 0, x: 50, scale: 0.8 },
						visible: { opacity: 1, x: 0, scale: 1 }
					}}
					initial="hidden"
					animate={mainControls}
					transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
				>
					<div className="relative mx-auto aspect-[4/3] w-full max-w-2xl overflow-hidden rounded-3xl shadow-2xl" style={{ border: '1px solid var(--border)', background: 'var(--card-bg)' }}>
						<div className="absolute inset-0 bg-gradient-to-tr from-indigo-100/40 via-transparent to-purple-100/40" />
						<img
							src="https://images.unsplash.com/photo-1525182008055-f88b95ff7980?q=80&w=1400&auto=format&fit=crop"
							alt="Reading hero"
							className="h-full w-full object-cover transition-transform duration-700 hover:scale-110"
						/>
						<div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-transparent" />
					</div>
				</motion.div>
			</div>

			{/* Category Chips Section */}
			<motion.div 
				className="relative mx-auto max-w-7xl px-4 sm:px-6 pb-12 sm:pb-16"
				variants={{
					hidden: { opacity: 0, y: 30 },
					visible: { opacity: 1, y: 0 }
				}}
				initial="hidden"
				animate={categoryControls}
				transition={{ duration: 0.8, delay: 0.6 }}
			>
				<div className="text-center mb-6 sm:mb-8">
					<h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2">Explore by Category</h2>
					<p className="text-gray-600 text-sm sm:text-base">Discover content that matches your interests</p>
				</div>
				<div className="flex flex-wrap justify-center gap-3 sm:gap-4">
					{loading ? (
						// Show loading skeleton for categories
						Array.from({ length: 6 }).map((_, index) => (
							<div
								key={index}
								className="animate-pulse rounded-2xl bg-gray-200 px-6 py-4 h-12 w-24"
							/>
						))
					) : (
						displayCategories.map((category, index) => (
							<motion.button
							key={category.name}
							onClick={() => onCategoryChange?.(category.name)}
							className={`group relative overflow-hidden rounded-xl sm:rounded-2xl px-4 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm font-semibold text-white shadow-2xl transition-all duration-300 hover:scale-105 sm:hover:scale-110 hover:shadow-3xl border border-white/20 ${
								selectedCategory === category.name 
									? 'ring-2 sm:ring-4 ring-white ring-opacity-50 scale-105' 
									: ''
							}`}
							style={{
								background: category.color?.includes('blue') ? 'linear-gradient(135deg, #3B82F6 0%, #4F46E5 100%)' :
											category.color?.includes('purple') ? 'linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%)' :
											category.color?.includes('emerald') ? 'linear-gradient(135deg, #10B981 0%, #14B8A6 100%)' :
											category.color?.includes('orange') ? 'linear-gradient(135deg, #F97316 0%, #EF4444 100%)' :
											category.color?.includes('green') ? 'linear-gradient(135deg, #22C55E 0%, #10B981 100%)' :
											category.color?.includes('yellow') ? 'linear-gradient(135deg, #EAB308 0%, #F97316 100%)' :
											category.color?.includes('rose') ? 'linear-gradient(135deg, #F43F5E 0%, #EC4899 100%)' :
											category.color?.includes('cyan') ? 'linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%)' :
											category.color?.includes('violet') ? 'linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%)' :
											category.color?.includes('amber') ? 'linear-gradient(135deg, #F59E0B 0%, #F97316 100%)' :
											'linear-gradient(135deg, #3B82F6 0%, #4F46E5 100%)'
							}}
							initial={{ opacity: 0, y: 20, scale: 0.8 }}
							animate={{ opacity: 1, y: 0, scale: 1 }}
							transition={{ delay: 0.7 + index * 0.1, duration: 0.5 }}
							whileHover={{ scale: 1.1, rotate: 2 }}
							whileTap={{ scale: 0.95 }}
						>
							{/* Category count badge */}
							{category.count && (
								<div className="absolute -top-2 -right-2 bg-black/30 backdrop-blur-sm rounded-full px-2 py-1 text-xs font-bold text-white border border-white/50 shadow-lg">
									{category.count}
								</div>
							)}
							
							{/* Main text */}
							<span className="relative z-10 text-sm sm:text-base font-bold tracking-wide text-white drop-shadow-lg" style={{ textShadow: '0 2px 4px rgba(0,0,0,0.5)' }}>
								{category.name}
							</span>
							
							{/* Hover effect overlay */}
							<div className="absolute inset-0 bg-white/20 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
							
							{/* Shine effect */}
							<div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
						</motion.button>
					))
					)}
				</div>
			</motion.div>
		</section>
	);
};

export default Hero;


