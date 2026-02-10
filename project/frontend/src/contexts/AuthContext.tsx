import { createContext, useContext, useState, ReactNode } from 'react';

type UserRole = 'operator' | 'corporate' | 'individual' | 'receiver' | 'admin' | 'manager';

interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  company?: string;
  depositBalance?: number;
  contractNumber?: string;
  phone?: string;
  station?: string;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => void;
  logout: () => void;
  isAuthenticated: boolean;
  register: (data: RegisterData) => void;
  token: string | null;
  authFetch: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;
}

interface RegisterData {
  name: string;
  email: string;
  password: string;
  role: 'corporate' | 'individual';
  company?: string;
  phone?: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const stored = typeof window !== 'undefined' ? localStorage.getItem('auth') : null;
  const initial = stored ? JSON.parse(stored) : null;
  const [user, setUser] = useState<User | null>(initial?.user || null);
  const [token, setToken] = useState<string | null>(initial?.token || null);

  const persistAuth = (nextUser: User | null, nextToken: string | null) => {
    setUser(nextUser);
    setToken(nextToken);
    if (nextUser && nextToken) {
      localStorage.setItem('auth', JSON.stringify({ user: nextUser, token: nextToken }));
    } else {
      localStorage.removeItem('auth');
    }
  };

  const login = async (email: string, password: string) => {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Login failed');
      }

      const data = await response.json();
      // Map backend snake_case to frontend camelCase
      const user: User = {
        ...data.user,
        depositBalance: data.user?.deposit_balance,
        contractNumber: data.user?.contract_number
      };

      persistAuth(user, data.token);
    } catch (error: any) {
      console.error('Login error:', error);
      alert(error.message);
    }
  };

  const register = async (data: RegisterData) => {
    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Registration failed');
      }

      const userData = await response.json();
      const user: User = {
        ...userData.user,
        depositBalance: userData.user?.deposit_balance,
        contractNumber: userData.user?.contract_number
      };
      persistAuth(user, userData.token);
      alert(`Регистрация успешна! Добро пожаловать, ${user.name}`);
    } catch (error: any) {
      console.error('Registration error:', error);
      alert(error.message);
    }
  };

  const logout = () => {
    persistAuth(null, null);
  };

  const authFetch = (input: RequestInfo | URL, init: RequestInit = {}) => {
    const headers = new Headers(init.headers || {});
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
    return fetch(input, { ...init, headers });
  };

  const isAuthenticated = !!user;

  console.log('Auth context state:', { user, isAuthenticated });

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated, register, token, authFetch }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
