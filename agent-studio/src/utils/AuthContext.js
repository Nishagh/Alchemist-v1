import React, { createContext, useContext, useState, useEffect } from 'react';
import { 
  onAuthStateChanged, 
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  sendPasswordResetEmail,
  GoogleAuthProvider,
  signInWithPopup,
  signInWithRedirect,
  getRedirectResult,
  setPersistence,
  browserLocalPersistence
} from 'firebase/auth';
import { auth } from './firebase';

// Create context
const AuthContext = createContext();

// Custom hook to use the auth context
export const useAuth = () => {
  return useContext(AuthContext);
};

// Provider component
export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Set up persistence to LOCAL (survives browser restarts)
  useEffect(() => {
    const setupPersistence = async () => {
      try {
        console.log("Setting Firebase auth persistence to LOCAL");
        await setPersistence(auth, browserLocalPersistence);
        console.log("Firebase persistence set successfully");
      } catch (error) {
        console.error("Error setting persistence:", error);
      }
    };
    
    setupPersistence();
  }, []);

  // Sign in with email and password
  const login = async (email, password) => {
    setError('');
    try {
      console.log("Logging in with email/password");
      const result = await signInWithEmailAndPassword(auth, email, password);
      console.log("Login successful:", result.user.email);
      return result;
    } catch (error) {
      console.error("Login error:", error);
      setError(error.message || "Failed to sign in");
      throw error;
    }
  };

  // Sign up with email and password
  const signup = (email, password) => {
    return createUserWithEmailAndPassword(auth, email, password);
  };

  // Sign in with Google popup
  const signInWithGoogle = async () => {
    setError('');
    try {
      const provider = new GoogleAuthProvider();
      // Add scopes if needed
      provider.addScope('https://www.googleapis.com/auth/userinfo.email');
      provider.addScope('https://www.googleapis.com/auth/userinfo.profile');
      
      // Optional: Specify additional OAuth parameters
      provider.setCustomParameters({
        prompt: 'select_account'
      });
      
      console.log("Starting Google Sign-In with popup");
      const result = await signInWithPopup(auth, provider);
      
      // This gives you a Google Access Token. You can use it to access the Google API.
      const credential = GoogleAuthProvider.credentialFromResult(result);
      const token = credential?.accessToken;
      
      // The signed-in user info
      const user = result.user;
      console.log("Google Sign-In successful:", user.email);
      
      return result;
    } catch (error) {
      console.error("Google Sign-In Error:", error);
      // Handle Errors here.
      const errorCode = error.code;
      const errorMessage = error.message;
      
      // The email of the user's account used.
      const email = error.customData?.email;
      
      // The AuthCredential type that was used.
      const credential = GoogleAuthProvider.credentialFromError(error);
      
      let userFriendlyMessage = "Google sign-in failed. Please try again.";
      
      if (errorCode === 'auth/popup-closed-by-user') {
        userFriendlyMessage = "Sign-in cancelled. You closed the popup window.";
      } else if (errorCode === 'auth/popup-blocked') {
        userFriendlyMessage = "Sign-in popup was blocked by your browser. Please allow popups for this site.";
      } else if (errorCode === 'auth/cancelled-popup-request') {
        userFriendlyMessage = "Sign-in was cancelled.";
      } else if (errorCode === 'auth/network-request-failed') {
        userFriendlyMessage = "Network error. Please check your internet connection.";
      }
      
      setError(userFriendlyMessage);
      throw { ...error, userFriendlyMessage };
    }
  };

  // Sign in with Google redirect (better for mobile)
  const signInWithGoogleRedirect = async () => {
    setError('');
    try {
      const provider = new GoogleAuthProvider();
      // Add scopes if needed
      provider.addScope('https://www.googleapis.com/auth/userinfo.email');
      provider.addScope('https://www.googleapis.com/auth/userinfo.profile');
      
      // Optional: Specify additional OAuth parameters
      provider.setCustomParameters({
        prompt: 'select_account'
      });
      
      console.log("Starting Google Sign-In with redirect");
      return await signInWithRedirect(auth, provider);
    } catch (error) {
      console.error("Google Sign-In Redirect Error:", error);
      setError("Google sign-in failed. Please try again.");
      throw error;
    }
  };

  // Process redirect result
  const processRedirectResult = async () => {
    try {
      const result = await getRedirectResult(auth);
      if (result) {
        console.log("Google Sign-In Redirect Result:", result.user.email);
      }
      return result;
    } catch (error) {
      console.error("Process Redirect Error:", error);
      setError("Failed to complete sign-in. Please try again.");
      throw error;
    }
  };

  // Sign out
  const logout = () => {
    setError('');
    return signOut(auth);
  };

  // Reset password
  const resetPassword = (email) => {
    setError('');
    return sendPasswordResetEmail(auth, email);
  };

  // Set up auth state observer on mount and clean up on unmount
  useEffect(() => {
    console.log("Setting up auth state observer");
    
    // First, verify if we already have a user in local storage
    const checkExistingUser = async () => {
      if (auth.currentUser) {
        console.log("Found existing user in auth state:", auth.currentUser.email);
        try {
          // Force token refresh to ensure we have a valid token
          await auth.currentUser.getIdToken(true);
          console.log("Token refreshed for existing user");
        } catch (error) {
          console.error("Error refreshing token for existing user:", error);
        }
      } else {
        console.log("No existing user found in auth state");
      }
    };
    
    // Call the check immediately
    checkExistingUser();
    
    // Then set up the auth state observer
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      console.log("Auth state changed. User:", user?.email || "No user");
      console.log("User details:", user ? {
        uid: user.uid,
        email: user.email,
        emailVerified: user.emailVerified,
        isAnonymous: user.isAnonymous,
        metadata: user.metadata,
        providerData: user.providerData
      } : "No user data");
      
      if (user) {
        // When user signs in, try to verify the token with the server
        try {
          const token = await user.getIdToken();
          
          // Try to call a simple API endpoint to verify the token
          const response = await fetch('/api/health', {
            headers: {
              Authorization: `Bearer ${token}`
            }
          });
          
          if (response.ok) {
            console.log("Successfully verified token with server");
          } else {
            console.warn(`Token verification failed with status: ${response.status}`);
            // Force token refresh if verification failed
            await user.getIdToken(true);
          }
        } catch (error) {
          console.error("Error verifying token with server:", error);
        }
      }
      
      setCurrentUser(user);
      setLoading(false);
    });

    // Check for redirect result on component mount
    processRedirectResult().catch(err => {
      console.error("Error processing redirect result:", err);
    });

    return unsubscribe;
  }, []);

  const value = {
    currentUser,
    login,
    signup,
    signInWithGoogle,
    signInWithGoogleRedirect,
    processRedirectResult,
    logout,
    resetPassword,
    loading,
    error
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
}; 