import React from 'react';

const CTASection = () => {
	return (
		<section className="relative mx-auto my-8 sm:my-12 max-w-7xl overflow-hidden rounded-2xl sm:rounded-3xl bg-gradient-to-r from-blue-600 to-cyan-600 px-4 sm:px-8 py-8 sm:py-12 text-white">
		<div className="absolute -left-10 -top-10 h-40 w-40 rounded-full" style={{ background: 'rgba(255,255,255,0.08)', filter: 'blur(24px)' }} />
		<div className="absolute -right-10 -bottom-10 h-40 w-40 rounded-full" style={{ background: 'rgba(255,255,255,0.04)', filter: 'blur(24px)' }} />
			<div className="relative flex flex-col items-center sm:items-start gap-4 sm:flex-row sm:items-center sm:justify-between">
				<div className="text-center sm:text-left">
					<h2 className="text-xl sm:text-2xl lg:text-3xl font-bold">Join thousands of readers and creators</h2>
					<p className="mt-1 text-white/90 text-sm sm:text-base">Get weekly highlights, pro tips and product updates.</p>
				</div>
				<form className="mt-3 flex flex-col sm:flex-row w-full max-w-md gap-2 sm:mt-0">
					<input type="email" placeholder="Enter your email" className="w-full rounded-full px-4 py-2 sm:py-3 text-black placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-white text-sm sm:text-base" />
					<button type="submit" className="rounded-full bg-white px-4 sm:px-6 py-2 sm:py-3 font-medium text-blue-700 transition hover:bg-blue-50 text-sm sm:text-base whitespace-nowrap">Subscribe</button>
				</form>
			</div>
		</section>
	);
};

export default CTASection;


