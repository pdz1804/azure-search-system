import React from 'react';
import { Link } from 'react-router-dom';
import { 
	DocumentTextIcon,
	EnvelopeIcon,
	PhoneIcon,
	MapPinIcon,
	HeartIcon
} from '@heroicons/react/24/outline';

const Footer = () => {
	const currentYear = new Date().getFullYear();

	return (
		<footer className="bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white">
			<div className="max-w-7xl mx-auto px-4 sm:px-6 py-12 sm:py-16">
				<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
					{/* Brand Section */}
					<div className="col-span-1 sm:col-span-2 lg:col-span-2 text-center sm:text-left">
						<Link to="/" className="flex items-center justify-center sm:justify-start space-x-2 mb-4 sm:mb-6 group">
							<div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-xl flex items-center justify-center shadow-lg group-hover:shadow-xl transition-all duration-300">
								<DocumentTextIcon className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
							</div>
							<span className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
								ArticleHub
							</span>
						</Link>
						<p className="text-gray-300 text-base sm:text-lg leading-relaxed max-w-md mb-4 sm:mb-6 mx-auto sm:mx-0">
							Elevate your knowledge with a modern, bright reading experience. Discover thoughtfully crafted insights from authors worldwide.
						</p>
						<div className="flex justify-center sm:justify-start space-x-3 sm:space-x-4">
							{/* GitHub */}
							<a href="https://github.com/pdz1804" target="_blank" rel="noopener noreferrer" className="w-8 h-8 sm:w-10 sm:h-10 bg-gray-700 rounded-lg flex items-center justify-center hover:bg-gray-600 transition-all duration-300 group">
								<svg className="w-4 h-4 sm:w-5 sm:h-5 text-gray-300 group-hover:text-white" fill="currentColor" viewBox="0 0 24 24">
									<path d="M12 0C5.374 0 0 5.373 0 12 0 17.302 3.438 21.8 8.207 23.387c.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/>
								</svg>
							</a>
							{/* LinkedIn */}
							<a href="https://www.linkedin.com/in/quangphunguyen/" target="_blank" rel="noopener noreferrer" className="w-8 h-8 sm:w-10 sm:h-10 bg-gray-700 rounded-lg flex items-center justify-center hover:bg-blue-700 transition-all duration-300 group">
								<svg className="w-4 h-4 sm:w-5 sm:h-5 text-gray-300 group-hover:text-white" fill="currentColor" viewBox="0 0 24 24">
									<path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
								</svg>
							</a>
							{/* Facebook */}
							<a href="https://www.facebook.com/zPhuDZz/" target="_blank" rel="noopener noreferrer" className="w-8 h-8 sm:w-10 sm:h-10 bg-gray-700 rounded-lg flex items-center justify-center hover:bg-blue-600 transition-all duration-300 group">
								<svg className="w-4 h-4 sm:w-5 sm:h-5 text-gray-300 group-hover:text-white" fill="currentColor" viewBox="0 0 24 24">
									<path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
								</svg>
							</a>
						</div>
					</div>

					{/* Quick Links */}
					<div className="text-center sm:text-left">
						<h3 className="text-base sm:text-lg font-semibold mb-4 sm:mb-6 text-white">Quick Links</h3>
						<ul className="space-y-2 sm:space-y-3">
							<li>
								<Link to="/" className="text-gray-300 hover:text-indigo-400 transition-colors duration-200 text-sm sm:text-base">
									Home
								</Link>
							</li>
							<li>
								<Link to="/blogs" className="text-gray-300 hover:text-indigo-400 transition-colors duration-200 text-sm sm:text-base">
									Blogs
								</Link>
							</li>
							<li>
								<Link to="/about" className="text-gray-300 hover:text-indigo-400 transition-colors duration-200 text-sm sm:text-base">
									About Us
								</Link>
							</li>
							<li>
								<Link to="/contact" className="text-gray-300 hover:text-indigo-400 transition-colors duration-200 text-sm sm:text-base">
									Contact
								</Link>
							</li>
						</ul>
					</div>

					{/* Contact Info */}
					<div className="text-center sm:text-left">
						<h3 className="text-base sm:text-lg font-semibold mb-4 sm:mb-6 text-white">Contact Info</h3>
						<div className="space-y-3 sm:space-y-4">
							<div className="flex items-center justify-center sm:justify-start space-x-2 sm:space-x-3">
								<EnvelopeIcon className="w-4 h-4 sm:w-5 sm:h-5 text-indigo-400 flex-shrink-0" />
								<a href="mailto:quangphunguyen1804@gmail.com" className="text-gray-300 hover:text-indigo-400 transition-colors duration-200 text-xs sm:text-sm break-all">
									quangphunguyen1804@gmail.com
								</a>
							</div>
							<div className="flex items-center justify-center sm:justify-start space-x-2 sm:space-x-3">
								<PhoneIcon className="w-4 h-4 sm:w-5 sm:h-5 text-indigo-400 flex-shrink-0" />
								<span className="text-gray-300 text-xs sm:text-sm">+84 000 000 000</span>
							</div>
							<div className="flex items-center justify-center sm:justify-start space-x-2 sm:space-x-3">
								<MapPinIcon className="w-4 h-4 sm:w-5 sm:h-5 text-indigo-400 flex-shrink-0" />
								<span className="text-gray-300 text-xs sm:text-sm">Ho Chi Minh City, Vietnam</span>
							</div>
						</div>
					</div>
				</div>

				{/* Bottom Section */}
				<div className="border-t border-gray-700 mt-8 sm:mt-12 pt-6 sm:pt-8">
					<div className="flex flex-col sm:flex-row justify-between items-center text-center sm:text-left">
						<p className="text-gray-400 text-xs sm:text-sm mb-3 sm:mb-0">
							© {currentYear} ArticleHub. All rights reserved.
						</p>
						<div className="flex items-center justify-center space-x-2 text-gray-400 text-xs sm:text-sm">
							<span>Made with</span>
							<HeartIcon className="w-3 h-3 sm:w-4 sm:h-4 text-red-500 animate-pulse" />
							<span>in Vietnam</span>
						</div>
					</div>
				</div>
			</div>
		</footer>
	);
};

export default Footer;
