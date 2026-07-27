import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authMe, authRefresh, type AuthUser } from '@/lib/auth';
import { safeStorage } from '@/lib/storage';

interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  setTokens: (access: string, refresh: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

const TOKEN_KEY = 'upcp_access_token';
const REFRESH_KEY = 'upcp_refresh_token';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(safeStorage.getItem(TOKEN_KEY));
  const [isLoading, setIsLoading] = useState(true);

  const loadUser = useCallback(async (accessToken: string) => {
    try {
      const userData = await authMe(accessToken);
      setUser(userData);
    } catch {
      // Token invalid, try refresh
      const refreshToken = safeStorage.getItem(REFRESH_KEY);
      if (refreshToken) {
        try {
          const tokens = await authRefresh(refreshToken);
          safeStorage.setItem(TOKEN_KEY, tokens.access_token);
          safeStorage.setItem(REFRESH_KEY, tokens.refresh_token);
          setToken(tokens.access_token);
          const userData = await authMe(tokens.access_token);
          setUser(userData);
        } catch {
          safeStorage.removeItem(TOKEN_KEY);
          safeStorage.removeItem(REFRESH_KEY);
          setToken(null);
          setUser(null);
        }
      } else {
        safeStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setUser(null);
      }
    }
  }, []);

  useEffect(() => {
    if (token) {
      loadUser(token).finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, [token, loadUser]);

  const setTokens = useCallback((access: string, refresh: string) => {
    safeStorage.setItem(TOKEN_KEY, access);
    safeStorage.setItem(REFRESH_KEY, refresh);
    setToken(access);
  }, []);

  const logout = useCallback(() => {
    safeStorage.removeItem(TOKEN_KEY);
    safeStorage.removeItem(REFRESH_KEY);
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !!user,
        setTokens,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
