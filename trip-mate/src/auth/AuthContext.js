import { createContext, useContext, useEffect, useState } from "react";
import { watchAuth, login as authLogin, register as authRegister, logout as authLogout, getAuthToken } from "../lib/auth";

const AuthContext = createContext({ 
  user: null, 
  loading: true, 
  isAuthed: false,
  login: () => {},
  register: () => {},
  logout: () => {}
});

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = watchAuth((u) => {
      setUser(u || null);
      setLoading(false);
    });
    return () => unsubscribe();
  }, []);

  const login = async (email, password) => {
    setLoading(true);
    const result = await authLogin(email, password);
    
    if (result.success) {
      // Immediately update user state instead of waiting for watchAuth
      setUser(result.user);
    }
    
    setLoading(false);
    return result;
  };

  const register = async (userData) => {
    setLoading(true);
    const result = await authRegister(userData);
    setLoading(false);
    return result;
  };

  const logout = () => {
    authLogout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      isAuthed: !!user,
      login,
      register,
      logout,
      token: getAuthToken()
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
