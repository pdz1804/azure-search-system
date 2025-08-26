import React from 'react';

const fmt = (v) => {
	if (v === null || v === undefined) return '0';
	if (typeof v === 'number') return v.toLocaleString();
	// try parse int from string like '10000+'
	const digits = String(v).replace(/[^0-9]/g, '');
	if (!digits) return v;
	try { return parseInt(digits, 10).toLocaleString(); } catch (e) { return v; }
};

const Stat = ({ label, value, loading }) => (
	<div className="rounded-xl sm:rounded-2xl border p-3 sm:p-5 text-center shadow-sm" style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}>
		{loading ? (
			<div className="animate-pulse">
				<div className="h-6 sm:h-8 bg-gray-200 rounded mb-2"></div>
				<div className="h-3 sm:h-4 bg-gray-200 rounded w-3/4 mx-auto"></div>
			</div>
		) : (
			<>
				<div className="text-xl sm:text-2xl lg:text-3xl font-extrabold" style={{ color: 'var(--text)' }}>{fmt(value)}</div>
				<div className="mt-1 text-xs sm:text-sm" style={{ color: 'var(--muted)' }}>{label}</div>
			</>
		)}
	</div>
);

const StatsBar = ({ totals = { articles: '500+', authors: '50+', total_views: '10000+', bookmarks: 0 }, loading = false }) => {
	return (
		<section className="mx-auto max-w-7xl px-4 sm:px-6">
			<div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
				<Stat label="Articles" value={totals.articles} loading={loading} />
				<Stat label="Authors" value={totals.authors} loading={loading} />
				<Stat label="Total Views" value={totals.total_views} loading={loading} />
				<Stat label="Bookmarks" value={totals.bookmarks} loading={loading} />
			</div>
		</section>
	);
};

export default StatsBar;


