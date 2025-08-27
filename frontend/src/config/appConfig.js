/**
 * Application Configuration
 * 
 * This file contains the configuration for the frontend application.
 * Change the APP_ID to configure which application instance this frontend represents.
 */

// Single point of configuration for the frontend app instance
// Change ONLY the fields below when creating/deploying another app instance
export const APP = {
  // Use the real app_id from your dataset (articles_transformed.json → Apps)
  id: '213f36bf-7999-43a7-ac4e-959bf166cdc3',
  name: 'Blog app',
  style: 'personal, informal, opinion-driven'
};

// Convenience exports
export const APP_ID = APP.id;
export const APP_NAME = APP.name;
export const APP_STYLE = APP.style;

export const getCurrentAppConfig = () => APP;
export const config = { APP, APP_ID, APP_NAME, APP_STYLE };

console.log(`🆔 Frontend App ID: ${APP_ID}`);
console.log(`📱 App Name: ${APP_NAME}`);
console.log(`🎨 App Style: ${APP_STYLE}`);
