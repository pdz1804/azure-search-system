import React from 'react';
import { Link } from 'react-router-dom';
import { 
  NewspaperIcon,
  HeartIcon,
  EnvelopeIcon,
  PhoneIcon,
  MapPinIcon
} from '@heroicons/react/24/outline';
import {
  FaceBookIcon,
  TwitterIcon,
  LinkedInIcon,
  YouTubeIcon,
  InstagramIcon
} from '../icons/SocialIcons';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  const footerLinks = {
    company: [
      { name: 'About Us', href: '/about' },
      { name: 'Our Team', href: '/team' },
      { name: 'Careers', href: '/careers' },
      { name: 'Contact', href: '/contact' }
    ],
    resources: [
      { name: 'Help Center', href: '/help' },
      { name: 'Guidelines', href: '/guidelines' },
      { name: 'FAQ', href: '/faq' },
      { name: 'API Documentation', href: '/api-docs' }
    ],
    legal: [
      { name: 'Privacy Policy', href: '/privacy' },
      { name: 'Terms of Service', href: '/terms' },
      { name: 'Cookie Policy', href: '/cookies' },
      { name: 'Copyright', href: '/copyright' }
    ],
    categories: [
      { name: 'Technology', href: '/category/technology' },
      { name: 'Science', href: '/category/science' },
      { name: 'Business', href: '/category/business' },
      { name: 'Health', href: '/category/health' }
    ]
  };

  const socialLinks = [
    {
      name: 'Facebook',
      href: 'https://facebook.com/articlehub',
      icon: FaceBookIcon,
      color: 'text-blue-600 hover:text-blue-700'
    },
    {
      name: 'Twitter',
      href: 'https://twitter.com/articlehub',
      icon: TwitterIcon,
      color: 'text-sky-500 hover:text-sky-600'
    },
    {
      name: 'LinkedIn',
      href: 'https://linkedin.com/company/articlehub',
      icon: LinkedInIcon,
      color: 'text-blue-700 hover:text-blue-800'
    },
    {
      name: 'YouTube',
      href: 'https://youtube.com/articlehub',
      icon: YouTubeIcon,
      color: 'text-red-600 hover:text-red-700'
    },
    {
      name: 'Instagram',
      href: 'https://instagram.com/articlehub',
      icon: InstagramIcon,
      color: 'text-pink-600 hover:text-pink-700'
    }
  ];

  return (
    <footer className="bg-gray-900 text-white">
      {/* Newsletter Section */}
      <div className="border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
            <div>
              <h3 className="text-2xl font-bold mb-2">Stay Updated</h3>
              <p className="text-gray-400">
                Get the latest articles and insights delivered to your inbox weekly.
              </p>
            </div>
            
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <input
                  type="email"
                  placeholder="Enter your email address"
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <button className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium">
                Subscribe
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Footer Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-8">
          {/* Brand Section */}
          <div className="lg:col-span-2">
            <Link to="/" className="flex items-center space-x-2 mb-4">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <NewspaperIcon className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold">ArticleHub</span>
            </Link>
            
            <p className="text-gray-400 mb-6 max-w-sm">
              Your go-to platform for discovering, reading, and sharing quality articles 
              from writers around the world. Join our community of knowledge seekers.
            </p>
            
            {/* Contact Info */}
            <div className="space-y-2 text-sm text-gray-400">
              <div className="flex items-center space-x-2">
                <EnvelopeIcon className="w-4 h-4" />
                <span>contact@articlehub.com</span>
              </div>
              <div className="flex items-center space-x-2">
                <PhoneIcon className="w-4 h-4" />
                <span>+1 (555) 123-4567</span>
              </div>
              <div className="flex items-center space-x-2">
                <MapPinIcon className="w-4 h-4" />
                <span>San Francisco, CA</span>
              </div>
            </div>
          </div>

          {/* Company Links */}
          <div>
            <h4 className="font-semibold mb-4">Company</h4>
            <ul className="space-y-2">
              {footerLinks.company.map((link) => (
                <li key={link.name}>
                  <Link
                    to={link.href}
                    className="text-gray-400 hover:text-white transition-colors text-sm"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h4 className="font-semibold mb-4">Resources</h4>
            <ul className="space-y-2">
              {footerLinks.resources.map((link) => (
                <li key={link.name}>
                  <Link
                    to={link.href}
                    className="text-gray-400 hover:text-white transition-colors text-sm"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Categories */}
          <div>
            <h4 className="font-semibold mb-4">Categories</h4>
            <ul className="space-y-2">
              {footerLinks.categories.map((link) => (
                <li key={link.name}>
                  <Link
                    to={link.href}
                    className="text-gray-400 hover:text-white transition-colors text-sm"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h4 className="font-semibold mb-4">Legal</h4>
            <ul className="space-y-2">
              {footerLinks.legal.map((link) => (
                <li key={link.name}>
                  <Link
                    to={link.href}
                    className="text-gray-400 hover:text-white transition-colors text-sm"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Bottom Section */}
      <div className="border-t border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            {/* Copyright */}
            <div className="flex items-center space-x-2 text-sm text-gray-400">
              <span>© {currentYear} ArticleHub. All rights reserved.</span>
              <span className="hidden md:inline">•</span>
              <span className="hidden md:inline">
                Made with <HeartIcon className="w-4 h-4 inline text-red-500" /> by the ArticleHub team
              </span>
            </div>

            {/* Social Links */}
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-400 mr-2">Follow us:</span>
              {socialLinks.map((social) => {
                const IconComponent = social.icon;
                return (
                  <a
                    key={social.name}
                    href={social.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`transition-colors ${social.color}`}
                    aria-label={`Follow us on ${social.name}`}
                  >
                    <IconComponent className="w-5 h-5" />
                  </a>
                );
              })}
            </div>
          </div>

          {/* Additional Info */}
          <div className="mt-4 pt-4 border-t border-gray-800 text-center">
            <p className="text-xs text-gray-500">
              This site is protected by reCAPTCHA and the Google{' '}
              <Link to="/privacy" className="underline hover:text-gray-400">
                Privacy Policy
              </Link>{' '}
              and{' '}
              <Link to="/terms" className="underline hover:text-gray-400">
                Terms of Service
              </Link>{' '}
              apply.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
