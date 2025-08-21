import React from 'react';

const Stat = ({ label, value }) => (
	<div className="rounded-2xl border border-gray-100 bg-white p-5 text-center shadow-sm">
		<div className="text-3xl font-extrabold text-gray-900">{value}</div>
		<div className="mt-1 text-sm text-gray-600">{label}</div>
	</div>
);

const StatsBar = ({ totals = { articles: 0, authors: 0, total_views: 0, bookmarks: 0 } }) => {
	return (
		<section className="mx-auto max-w-7xl px-6">
			<div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
				<Stat label="Articles" value={totals.articles} />
				<Stat label="Authors" value={totals.authors} />
				<Stat label="Total Views" value={totals.total_views} />
				<Stat label="Bookmarks" value={totals.bookmarks} />
			</div>
		</section>
	);
};

export default StatsBar;


