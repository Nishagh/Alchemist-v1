/**
 * Firebase Authentication Configuration
 * This file configures and enables various authentication methods in Firebase
 */

const { admin } = require('./firebase-admin');

/**
 * Configure Firebase Authentication Providers
 * This function should be called during server initialization to set up auth providers
 */
const configureFirebaseAuth = async () => {
  try {
    // Get the current authentication configuration
    const authConfig = await admin.auth().getProviderConfigs();
    
    // Check if Google provider is already configured
    const googleProvider = authConfig.find(provider => provider.providerId === 'google.com');
    
    if (!googleProvider) {
      console.log('Configuring Google authentication provider...');
      
      // Enable Google authentication with correct client ID
      // This should match the client ID in your Google Cloud Console
      await admin.auth().updateProviderConfig('google.com', {
        enabled: true,
        client_id: process.env.GOOGLE_CLIENT_ID || '103214520240448237488-lb29l43khpqnqnk7rfoiokbvsmvj5f7i.apps.googleusercontent.com'
      });
      
      console.log('Google authentication provider configured successfully');
    } else {
      console.log('Google authentication provider already configured');
    }
    
    // Additional providers can be configured here (Facebook, Twitter, GitHub, etc.)
    
  } catch (error) {
    console.error('Error configuring Firebase authentication:', error);
    // Continue execution even if configuration fails
  }
};

module.exports = {
  configureFirebaseAuth
}; 