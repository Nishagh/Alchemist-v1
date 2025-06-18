// Firebase Admin SDK initialization for client-side references
// Note: This file should NOT be used to make actual Admin SDK calls from the browser
// It's only for TypeScript type definitions and references
// Actual Firebase Admin operations should be done server-side

// Project configuration from hardcoded values
const firebaseAdminConfig = {
  projectId: "alchemist-e69bb",
  storageBucket: "alchemist-e69bb.appspot.com"
};

// Export types and references without actually initializing Admin SDK
// This avoids security issues with including service account credentials in client code
export const adminConfig = firebaseAdminConfig;

// For TypeScript type safety, you can export mock objects with the same shape
// as the actual admin services would have, but without functionality
export const adminAuth = { /* mock implementation */ };
export const adminDb = { /* mock implementation */ };
export const adminStorage = { /* mock implementation */ };
export const adminApp = { /* mock implementation */ }; 