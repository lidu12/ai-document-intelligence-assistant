"use client";

/**
 * Global Authentication Context & Provider
 * Manages user login state, token persistence in localStorage, and session restoration.
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { authApi, User } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Fetch the current user profile using the stored JWT token
  const refreshProfile = useCallback(async () => {
    try {
      const profile = await authApi.getProfile();
      setUser(profile);
    } catch (error) {
      console.warn("Failed to fetch user profile, clearing stale session:", error);
      localStorage.removeItem("access_token");
      setUser(null);
      setToken(null);
    }
  }, []);

  // Restore session from localStorage on initial page mount
  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem("access_token");
      if (storedToken) {
        setToken(storedToken);
        await refreshProfile();
      }
      setIsLoading(false);
    };

    initializeAuth();
  }, [refreshProfile]);

  // Handle user login
  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const tokenResponse = await authApi.login({ email, password });
      localStorage.setItem("access_token", tokenResponse.access_token);
      setToken(tokenResponse.access_token);
      await refreshProfile();
    } finally {
      setIsLoading(false);
    }
  };

  // Handle user registration
  const register = async (email: string, password: string, fullName?: string) => {
    setIsLoading(true);
    try {
      await authApi.register({ email, password, full_name: fullName });
      // Automatically log the user in following successful registration
      await login(email, password);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle user logout
  const logout = () => {
    localStorage.removeItem("access_token");
    setUser(null);
    setToken(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

// Custom Hook for consuming the AuthContext with safety check
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
