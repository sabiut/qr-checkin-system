import { createContext, useState, useEffect, ReactNode } from 'react';

interface User {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (userData: User, token: string) => void;
  logout: () => void;
}

// Create context with default value
export const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  isAuthenticated: false,
  login: () => {},
  logout: () => {},
});

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [isBrowser, setIsBrowser] = useState<boolean>(false);

  // Check if we're in a browser environment
  useEffect(() => {
    setIsBrowser(true);
    setLoading(false);
  }, []);

  // Check for existing user data and token on mount - separate effect to run after browser check
  useEffect(() => {
    if (!isBrowser) return;
    
    try {
      const storedToken = localStorage.getItem('auth_token');
      const storedUserData = localStorage.getItem('user_data');
      
      if (storedToken && storedUserData) {
        const userData = JSON.parse(storedUserData) as User;
        setUser(userData);
        setToken(storedToken);
        setIsAuthenticated(true);
      }
    } catch (error) {
      console.error('Error parsing stored user data:', error);
      if (isBrowser) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_data');
      }
    }
  }, [isBrowser]);

  // Login function
  const login = (userData: User, authToken: string) => {
    setUser(userData);
    setToken(authToken);
    setIsAuthenticated(true);
    if (isBrowser) {
      try {
        localStorage.setItem('auth_token', authToken);
        localStorage.setItem('user_data', JSON.stringify(userData));
      } catch (error) {
        console.error('Error saving auth data:', error);
      }
    }
  };

  // Logout function
  const logout = async () => {
    try {
      // Call the logout API only if in browser and token exists
      if (isBrowser && token) {
        try {
          await fetch(`${import.meta.env.VITE_API_URL}/api/auth/logout/`, {
            method: 'POST',
            headers: {
              'Authorization': `Token ${token}`,
              'Content-Type': 'application/json',
            },
          });
        } catch (apiError) {
          console.error('Error calling logout API:', apiError);
        }
      }
    } catch (error) {
      console.error('Error during logout:', error);
    } finally {
      // Clear local state and storage
      setUser(null);
      setToken(null);
      setIsAuthenticated(false);
      
      if (isBrowser) {
        try {
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user_data');
        } catch (storageError) {
          console.error('Error clearing local storage:', storageError);
        }
      }
    }
  };

  if (loading) {
    // Show a loading indicator or return null
    return null;
  }

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};