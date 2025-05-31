```tsx
import React, { createContext, useState, useEffect, ReactNode, useMemo, useCallback } from 'react';
import {
  authInstance,
  User,
  onAuthStateChanged as onFirebaseAuthStateChanged,
  firebaseSignOut,
  getIdToken as getFirebaseIdToken,
} from '../services/firebaseService';

interface AuthContextType {
  currentUser: User | null;
  idToken: string | null;
  isLoading: boolean;
  isInitialized: boolean; // To know when initial auth check is done
  error: Error | null;
  signOut: () => Promise<void>;
  refreshIdToken: (forceRefresh?: boolean) => Promise<string | null>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [idToken, setIdToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true); // True initially for auth check
  const [isInitialized, setIsInitialized] = useState(false); // Tracks if the initial onAuthStateChanged has fired
  const [error, setError] = useState<Error | null>(null);

  const handleUser = useCallback(async (user: User | null) => {
    if (user) {
      setCurrentUser(user);
      try {
        const token = await getFirebaseIdToken(user);
        setIdToken(token);
      } catch (e) {
        console.error("AuthContext: Error getting ID token:", e);
        setError(e instanceof Error ? e : new Error(String(e)));
        await firebaseSignOut(authInstance); // Sign out if token fails
        setCurrentUser(null);
        setIdToken(null);
      }
    } else {
      setCurrentUser(null);
      setIdToken(null);
    }
    setIsLoading(false);
    setIsInitialized(true); // Mark initial auth check complete
  }, []);

  useEffect(() => {
    const unsubscribe = onFirebaseAuthStateChanged(
      authInstance,
      handleUser, // Success callback
      (authError) => { // Error callback for onAuthStateChanged
        console.error("AuthContext: Auth state error:", authError);
        setError(authError);
        setCurrentUser(null);
        setIdToken(null);
        setIsLoading(false);
        setIsInitialized(true); // Mark initial auth check complete even on error
      }
    );

    return () => unsubscribe(); // Cleanup subscription on unmount
  }, [handleUser]);

  const signOut = async () => {
    setIsLoading(true);
    setError(null); // Clear previous errors
    try {
      await firebaseSignOut(authInstance);
      // State (currentUser, idToken) will be updated by the onAuthStateChanged listener.
      // isLoading will be set to false by handleUser.
    } catch (e) {
      console.error("AuthContext: Sign out error:", e);
      setError(e instanceof Error ? e : new Error(String(e)));
      setIsLoading(false); // Ensure loading state is reset on error
    }
  };

  const refreshIdToken = useCallback(async (forceRefresh: boolean = false): Promise<string | null> => {
    if (currentUser) {
      try {
        const token = await getFirebaseIdToken(currentUser, forceRefresh);
        setIdToken(token); // Update context state with new token
        return token;
      } catch (e) {
        console.error("AuthContext: Error refreshing ID token:", e);
        setError(e instanceof Error ? e : new Error(String(e)));
        // Critical token refresh failure, likely session expired or revoked. Sign out.
        await signOut(); // This will trigger onAuthStateChanged to nullify user
        return null;
      }
    }
    return null;
  }, [currentUser, signOut]); // Added signOut to dependency array

  const value = useMemo(() => ({
    currentUser,
    idToken,
    isLoading,
    isInitialized,
    error,
    signOut,
    refreshIdToken,
  }), [currentUser, idToken, isLoading, isInitialized, error, signOut, refreshIdToken]);


  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
```
