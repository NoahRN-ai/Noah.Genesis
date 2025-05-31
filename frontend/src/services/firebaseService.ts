```typescript
import { initializeApp, FirebaseApp, getApp, getApps } from 'firebase/app'; // Added getApp, getApps
import {
  getAuth,
  Auth,
  User,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut as firebaseSignOut, // renamed to avoid conflict
  onAuthStateChanged,
  getIdToken,
  GoogleAuthProvider,
  signInWithPopup,
  updateProfile as firebaseUpdateProfile, // For updating Firebase User display name
} from 'firebase/auth';

// Your web app's Firebase configuration - USE ENVIRONMENT VARIABLES
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  // measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID, // Optional
};

// Initialize Firebase (ensuring it's only done once)
let app: FirebaseApp;
if (!getApps().length) {
  try {
    app = initializeApp(firebaseConfig);
    console.log("Firebase App Initialized successfully.");
  } catch (error) {
    console.error("Error initializing Firebase App:", error);
    // In a real app, you might want to set a global error state or throw
    // to prevent the app from running in a broken state.
    // For now, this will allow other modules to import even if init fails,
    // but subsequent Firebase calls would fail.
  }
} else {
  app = getApp(); // Get the default app if already initialized
  console.log("Firebase App already initialized.");
}


const authInstance: Auth = getAuth(app);
const googleProvider: GoogleAuthProvider = new GoogleAuthProvider();


export {
  app as firebaseApp, // Export the app instance if needed elsewhere
  authInstance,
  User,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  firebaseSignOut,
  onAuthStateChanged,
  getIdToken,
  googleProvider,
  signInWithPopup,
  firebaseUpdateProfile,
};
```
