import { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);
const TOKEN_KEY = 'plantdoctor_token';
const USER_KEY = 'plantdoctor_user';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem(USER_KEY);
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));

  const login = async (phone, password) => {
    const res = await axios.post('/api/v1/auth/login', { phone, password });
    setToken(res.data.token);
    setUser(res.data.user);
    localStorage.setItem(TOKEN_KEY, res.data.token);
    localStorage.setItem(USER_KEY, JSON.stringify(res.data.user));
    return res.data;
  };

  const register = async (phone, password, name) => {
    const res = await axios.post('/api/v1/auth/register', { phone, password, name });
    setToken(res.data.token);
    setUser(res.data.user);
    localStorage.setItem(TOKEN_KEY, res.data.token);
    localStorage.setItem(USER_KEY, JSON.stringify(res.data.user));
    return res.data;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  };

  const getToken = () => token;

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, getToken }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() { return useContext(AuthContext); }
