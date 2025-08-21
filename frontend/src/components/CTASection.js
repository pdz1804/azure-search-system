import React from 'react';

const CTASection = () => {
	return (
		<section className="relative mx-auto my-12 max-w-7xl overflow-hidden rounded-3xl bg-gradient-to-r from-blue-600 to-cyan-600 px-8 py-12 text-white">
			<div className="absolute -left-10 -top-10 h-40 w-40 rounded-full bg-white/20 blur-2xl" />
			<div className="absolute -right-10 -bottom-10 h-40 w-40 rounded-full bg-white/10 blur-2xl" />
			<div className="relative flex flex-col items-start gap-4 sm:flex-row sm:items-center sm:justify-between">
				<div>
					<h2 className="text-2xl font-bold sm:text-3xl">Join thousands of readers and creators</h2>
					<p className="mt-1 text-white/90">Get weekly highlights, pro tips and product updates.</p>
				</div>
				<form className="mt-3 flex w-full max-w-md gap-2 sm:mt-0">
					<input type="email" placeholder="Enter your email" className="w-full rounded-full px-4 py-3 text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-white" />
					<button type="submit" className="rounded-full bg-white px-6 py-3 font-medium text-blue-700 transition hover:bg-blue-50">Subscribe</button>
				</form>
			</div>
		</section>
	);
};

export default CTASection;


