```typescript
import { initializeApp, FirebaseApp, getApp, getApps } from 'firebase/app';
import {
  getAuth,
  Auth,
  User,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  getIdToken,
  GoogleAuthProvider,
  signInWithPopup,
  updateProfile as firebaseUpdateProfile, // For updating Firebase User display name
} from 'firebase/auth';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

let app: FirebaseApp;
if (!getApps().length) {
  try {
    app = initializeApp(firebaseConfig);
    console.info("Firebase App Initialized successfully.");
  } catch (error) {
    console.error("CRITICAL: Error initializing Firebase App:", error);
    // In a production app, you might want to render an error page or prevent app load.
  }
} else {
  app = getApp();
}

const authInstance: Auth = getAuth(app!); // app should be initialized
const googleProvider: GoogleAuthProvider = new GoogleAuthProvider();

export {
  app as firebaseApp,
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
