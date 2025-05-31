```tsx
import React, { createContext, useState, useEffect, ReactNode, useMemo, useCallback } from 'react';
import {
  authInstance,
  User as FirebaseUser, // Renamed to avoid naming conflict if we define our own User type
  onAuthStateChanged as onFirebaseAuthStateChanged,
  firebaseSignOut,
  getIdToken as getFirebaseIdToken,
} from '../services/firebaseService';
import { UserInfo } from '../types/api'; // Our app-specific UserInfo type

interface AuthContextType {
  currentUser: UserInfo | null; // Using our app's UserInfo type
  firebaseUser: FirebaseUser | null; // Raw Firebase user object if needed
  idToken: string | null;
  isLoading: boolean; // True during initial auth check or auth operations
  isInitialized: boolean; // True after the initial onAuthStateChanged has run
  error: Error | null;
  signOut: () => Promise<void>;
  refreshIdToken: (forceRefresh?: boolean) => Promise<string | null>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<UserInfo | null>(null);
  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);
  const [idToken, setIdToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const mapFirebaseUserToUserInfo = (fbUser: FirebaseUser | null): UserInfo | null => {
    if (!fbUser) return null;
    return {
      uid: fbUser.uid,
      email: fbUser.email,
      displayName: fbUser.displayName,
      photoURL: fbUser.photoURL,
      emailVerified: fbUser.emailVerified,
    };
  };

  const handleUserChange = useCallback(async (fbUser: FirebaseUser | null) => {
    setIsLoading(true); // Set loading true at start of handling change
    setError(null);
    if (fbUser) {
      setFirebaseUser(fbUser);
      const appUserInfo = mapFirebaseUserToUserInfo(fbUser);
      setCurrentUser(appUserInfo);
      try {
        const token = await getFirebaseIdToken(fbUser);
        setIdToken(token);
      } catch (e) {
        console.error("AuthContext: Error getting ID token:", e);
        setError(e instanceof Error ? e : new Error(String(e)));
        // Critical token failure: sign out user from Firebase and clear app state
        await firebaseSignOut(authInstance);
        setFirebaseUser(null);
        setCurrentUser(null);
        setIdToken(null);
      }
    } else {
      setFirebaseUser(null);
      setCurrentUser(null);
      setIdToken(null);
    }
    setIsLoading(false);
    if (!isInitialized) setIsInitialized(true);
  }, [isInitialized]); // isInitialized is included to ensure it runs at least once

  useEffect(() => {
    const unsubscribe = onFirebaseAuthStateChanged(
      authInstance,
      handleUserChange,
      (authError) => {
        console.error("AuthContext: Auth state error listener:", authError);
        setError(authError);
        setFirebaseUser(null);
        setCurrentUser(null);
        setIdToken(null);
        setIsLoading(false);
        if (!isInitialized) setIsInitialized(true);
      }
    );
    return () => unsubscribe();
  }, [handleUserChange, isInitialized]); // Ensure effect re-runs if isInitialized state was key

  const signOut = async () => {
    setIsLoading(true);
    setError(null);
    try {
      await firebaseSignOut(authInstance);
      // onFirebaseAuthStateChanged will set user to null and trigger re-renders
    } catch (e) {
      console.error("AuthContext: Sign out error:", e);
      setError(e instanceof Error ? e : new Error(String(e)));
      // Ensure isLoading is reset even if signOut itself throws an error locally
      // though onAuthStateChanged should still fire and update loading.
      setIsLoading(false);
    }
  };

  const refreshIdToken = useCallback(async (forceRefresh: boolean = true): Promise<string | null> => {
    // Always force refresh when this is called explicitly to ensure a fresh token.
    if (firebaseUser) {
      try {
        const token = await getFirebaseIdToken(firebaseUser, forceRefresh);
        setIdToken(token);
        return token;
      } catch (e) {
        console.error("AuthContext: Error refreshing ID token:", e);
        setError(e instanceof Error ? e : new Error(String(e)));
        await signOut(); // Force sign out on critical token refresh failure
        return null;
      }
    }
    return null;
  }, [firebaseUser, signOut]);

  const value = useMemo(() => ({
    currentUser,
    firebaseUser,
    idToken,
    isLoading,
    isInitialized,
    error,
    signOut,
    refreshIdToken,
  }), [currentUser, firebaseUser, idToken, isLoading, isInitialized, error, signOut, refreshIdToken]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
```
