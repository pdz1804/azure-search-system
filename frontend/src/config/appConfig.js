/**
 * Application Configuration
 * 
 * This file contains the configuration for the frontend application.
 * Configuration is loaded from environment variables to support multiple app instances.
 * 
 * Environment files:
 * - .env.local (local development overrides)
 * - .env.blog (blog app instance)
 * - .env.news (news app instance) 
 * - .env.tech (tech app instance)
 */

// Load configuration from environment variables with fallbacks
const getEnvConfig = () => {
  // Check if we have environment variables
  if (process.env.REACT_APP_ID) {
    return {
      id: process.env.REACT_APP_ID,
      name: process.env.REACT_APP_NAME || 'Default App',
      style: process.env.REACT_APP_STYLE || 'default style',
      apiUrl: process.env.REACT_APP_API_URL,
      debug: process.env.REACT_APP_DEBUG === 'true',
      enableAnalytics: process.env.REACT_APP_ENABLE_ANALYTICS === 'true'
    };
  }
  
  // Fallback to default configuration (for development)
  console.warn('⚠️ No REACT_APP_ID found in environment variables. Using default configuration.');
  return {
    id: '213f36bf-7999-43a7-ac4e-959bf166cdc3',
    name: 'Blog app',
    style: 'personal, informal, opinion-driven',
    apiUrl: 'http://localhost:8001/api',
    debug: true,
    enableAnalytics: false
  };
};

// Single point of configuration for the frontend app instance
export const APP = getEnvConfig();

// Convenience exports
export const APP_ID = APP.id;
export const APP_NAME = APP.name;
export const APP_STYLE = APP.style;
export const API_URL = APP.apiUrl;
export const DEBUG = APP.debug;
export const ENABLE_ANALYTICS = APP.enableAnalytics;

export const getCurrentAppConfig = () => APP;
export const config = { 
  APP, 
  APP_ID, 
  APP_NAME, 
  APP_STYLE, 
  API_URL, 
  DEBUG, 
  ENABLE_ANALYTICS 
};

// Log configuration for debugging
if (DEBUG) {
  console.log(`🆔 Frontend App ID: ${APP_ID}`);
  console.log(`📱 App Name: ${APP_NAME}`);
  console.log(`🎨 App Style: ${APP_STYLE}`);
  console.log(`🔗 API URL: ${API_URL}`);
  console.log(`🐛 Debug Mode: ${DEBUG}`);
  console.log(`📊 Analytics: ${ENABLE_ANALYTICS}`);
}
