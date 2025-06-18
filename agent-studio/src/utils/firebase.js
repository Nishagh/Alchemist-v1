// Firebase app initialization
import { initializeApp } from 'firebase/app';
import { getAuth, connectAuthEmulator, onAuthStateChanged } from 'firebase/auth';
import { getStorage } from 'firebase/storage';
import { getFirestore } from 'firebase/firestore';

// Firebase configuration - with fallback to hardcoded values
const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY || "AIzaSyC9MLh9IiFIcH5RJRVLJlrTXNI5s03r4AE",
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN || "alchemist-e69bb.firebaseapp.com",
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID || "alchemist-e69bb",
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET || "alchemist-e69bb.appspot.com",
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID || "103214520240448237488",
  appId: process.env.REACT_APP_FIREBASE_APP_ID || "1:851487020021:web:527efbdbe1ded9aa2686bc"
};

console.log("Firebase configuration:", firebaseConfig);

// Declare Firebase service variables
let app;
let auth;
let storage;
let db;

// Initialize Firebase
try {
  console.log("Initializing Firebase app");
  app = initializeApp(firebaseConfig);

  // Initialize Firebase services
  console.log("Initializing Firebase auth");
  auth = getAuth(app);
  
  // Set up auth state observer to log initialization issues
  const unsubscribe = onAuthStateChanged(auth, 
    (user) => {
      console.log("Firebase auth initialization successful");
      console.log("Initial auth state:", user ? `User logged in: ${user.email}` : "No user logged in");
      unsubscribe(); // Remove the observer after initial check
    },
    (error) => {
      console.error("Firebase auth initialization error:", error);
    }
  );
  
  console.log("Initializing Firebase storage");
  storage = getStorage(app);
  
  console.log("Initializing Firebase firestore");
  db = getFirestore(app);
  
  console.log("Firebase services initialized successfully");
  
  // For local development, connect to emulators if needed
  if (process.env.REACT_APP_USE_FIREBASE_EMULATORS === 'true') {
    console.log("Connecting to Firebase emulators");
    connectAuthEmulator(auth, 'http://localhost:9099');
    // Add other emulator connections as needed
  }
} catch (error) {
  console.error("Error initializing Firebase:", error);
  // Create dummy objects as fallback to prevent crashes
  app = {};
  auth = { currentUser: null };
  storage = {};
  db = {};
}

// Export the Firebase services
export { app, auth, storage, db }; 