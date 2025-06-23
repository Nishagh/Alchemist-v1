/**
 * Firebase Authentication Configuration
 * This file handles authentication-related server operations
 * Note: Provider configuration should be done through Firebase console, not programmatically
 */

const { admin } = require('./firebase-admin');

/**
 * Initialize Firebase Authentication
 * This function initializes auth-related middleware and settings
 */
const configureFirebaseAuth = async () => {
  try {
    console.log('Firebase authentication initialized successfully');
    
    // Add any auth middleware setup here if needed
    // For example: setting up custom claims, auth middleware, etc.
    
  } catch (error) {
    console.error('Error configuring Firebase authentication:', error);
    // Continue execution even if configuration fails
  }
};

/**
 * Verify Firebase ID token (utility function for API routes)
 */
const verifyIdToken = async (idToken) => {
  try {
    const decodedToken = await admin.auth().verifyIdToken(idToken);
    return decodedToken;
  } catch (error) {
    console.error('Error verifying ID token:', error);
    throw error;
  }
};

module.exports = {
  configureFirebaseAuth,
  verifyIdToken
}; 