/**
 * Authentication Debugging Utilities
 * This file provides tools to help debug authentication issues
 */

import { auth } from './firebase';

// Function to check and log the current authentication state
export const debugAuthState = async () => {
  try {
    const currentUser = auth.currentUser;
    
    console.group('🔐 Auth Debugging Information');
    console.log('Current user:', currentUser);
    
    if (currentUser) {
      console.log('User ID:', currentUser.uid);
      console.log('Email:', currentUser.email);
      console.log('Email verified:', currentUser.emailVerified);
      console.log('Provider data:', currentUser.providerData);
      
      // Check if token is valid and not expired
      try {
        const token = await currentUser.getIdToken();
        console.log('Token successfully retrieved (truncated):', token.substring(0, 20) + '...');
        
        // Parse the token to check expiry
        const tokenParts = token.split('.');
        if (tokenParts.length === 3) {
          const payload = JSON.parse(atob(tokenParts[1]));
          const expiry = new Date(payload.exp * 1000);
          const now = new Date();
          
          console.log('Token expiry:', expiry);
          console.log('Current time:', now);
          console.log('Token expired:', expiry < now);
        }
      } catch (error) {
        console.error('Error getting token:', error);
      }
    } else {
      console.log('No user is currently signed in');
      
      // Check if there's data in localStorage that might indicate a stale session
      const firebaseLocalStorageKeys = Object.keys(localStorage).filter(key => 
        key.startsWith('firebase:') || key.includes('firebase')
      );
      
      if (firebaseLocalStorageKeys.length > 0) {
        console.log('Found Firebase localStorage items:', firebaseLocalStorageKeys);
        console.log('This might indicate a stale session');
      } else {
        console.log('No Firebase localStorage data found');
      }
    }
    
    console.log('Auth object initialized:', !!auth);
    console.groupEnd();
    
    return {
      isAuthenticated: !!currentUser,
      user: currentUser
    };
  } catch (error) {
    console.error('Error in debugAuthState:', error);
    return {
      isAuthenticated: false,
      error
    };
  }
};

// Function to check API connectivity with auth token
export const testAuthenticatedRequest = async (endpoint = '/api/health') => {
  try {
    const currentUser = auth.currentUser;
    if (!currentUser) {
      console.error('Cannot test authenticated request - no user logged in');
      return { success: false, error: 'No user logged in' };
    }
    
    const token = await currentUser.getIdToken();
    
    console.log(`Testing authenticated request to ${endpoint}...`);
    const response = await fetch(endpoint, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    const data = await response.json();
    
    console.log('Response status:', response.status);
    console.log('Response data:', data);
    
    return {
      success: response.ok,
      status: response.status,
      data
    };
  } catch (error) {
    console.error('Error testing authenticated request:', error);
    return {
      success: false,
      error
    };
  }
};

// Function to clear auth state and localStorage for testing
export const resetAuthState = () => {
  try {
    console.log('Attempting to reset auth state...');
    
    // Sign out
    auth.signOut();
    
    // Clear any Firebase related localStorage items
    const firebaseLocalStorageKeys = Object.keys(localStorage).filter(key => 
      key.startsWith('firebase:') || key.includes('firebase')
    );
    
    firebaseLocalStorageKeys.forEach(key => {
      localStorage.removeItem(key);
      console.log(`Removed localStorage item: ${key}`);
    });
    
    console.log('Auth state reset completed');
    return true;
  } catch (error) {
    console.error('Error resetting auth state:', error);
    return false;
  }
}; 