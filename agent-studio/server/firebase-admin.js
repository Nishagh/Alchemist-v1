// Server-side Firebase Admin SDK initialization
const admin = require('firebase-admin');
const path = require('path');
const fs = require('fs');

// Function to get Firebase credentials
const getFirebaseCredentials = () => {
  // Option 1: Check for credentials mounted as a file from Secret Manager
  const secretPath = process.env.FIREBASE_CREDENTIALS || '/firebase/credentials.json';
  if (fs.existsSync(secretPath)) {
    console.log(`Loading Firebase credentials from ${secretPath}`);
    return JSON.parse(fs.readFileSync(secretPath, 'utf8'));
  }
  
  // Option 2: Check for credentials in the project directory (local development)
  const localPath = path.join(__dirname, '../firebase-credentials.json');
  if (fs.existsSync(localPath)) {
    console.log(`Loading Firebase credentials from ${localPath}`);
    return JSON.parse(fs.readFileSync(localPath, 'utf8'));
  }
  
  // Option 3: Use project ID from environment variables (for simplified setup)
  const projectId = process.env.FIREBASE_PROJECT_ID;
  if (projectId) {
    console.log(`Using Firebase project ID from environment: ${projectId}`);
    return { project_id: projectId };
  }
  
  console.error('No Firebase credentials found. Please provide credentials.');
  return null;
};

// Initialize Firebase Admin
const initializeFirebase = () => {
  if (admin.apps.length > 0) {
    return; // Already initialized
  }

  // Get credentials
  const credentials = getFirebaseCredentials();
  
  if (credentials) {
    // If we have a full service account credential
    if (credentials.private_key) {
      admin.initializeApp({
        credential: admin.credential.cert(credentials),
        storageBucket: `${credentials.project_id}.appspot.com`
      });
      console.log('Firebase Admin initialized with service account credentials');
    } 
    // If we just have a project ID (for simplified access)
    else if (credentials.project_id) {
      admin.initializeApp({
        projectId: credentials.project_id,
        storageBucket: `${credentials.project_id}.appspot.com`
      });
      console.log('Firebase Admin initialized with application default credentials');
    }
  } else {
    // For cloud deployment without credentials file, use default application credentials
    const projectId = process.env.FIREBASE_PROJECT_ID || 'alchemist-e69bb';
    admin.initializeApp({
      projectId: projectId,
      storageBucket: `${projectId}.appspot.com`
    });
    console.log('Firebase Admin initialized with default application credentials for cloud deployment');
  }
};

// Initialize Firebase
initializeFirebase();

// Export Firebase Admin services
const auth = admin.auth();
const db = admin.firestore();
const storage = admin.storage();

module.exports = {
  admin,
  auth,
  db,
  storage
}; 