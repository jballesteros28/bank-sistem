// src/context/AuthProvider.jsx
import { useEffect, useMemo, useState } from "react";
import { AuthContext } from "./authContext";

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);

  // 🔹 Cargar sesión persistida al iniciar la app
  useEffect(() => {
    const token = localStorage.getItem("bank.jwt");
    const storedUser = localStorage.getItem("bank.user");

    if (token && storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch {
        // Si el JSON falla (p. ej. se corrompió), limpiamos sesión
        localStorage.removeItem("bank.jwt");
        localStorage.removeItem("bank.user");
      }
    }
  }, []);

  // 🔹 Login (guardar token + usuario)
  const login = (token, userData) => {
    localStorage.setItem("bank.jwt", token);
    localStorage.setItem("bank.user", JSON.stringify(userData));
    setUser(userData);
  };

  // 🔹 Logout (limpiar todo)
  const logout = () => {
    localStorage.removeItem("bank.jwt");
    localStorage.removeItem("bank.user");
    setUser(null);
  };

  // 🔹 Memoizar el contexto (evita renders innecesarios)
  const value = useMemo(() => ({ user, setUser, login, logout }), [user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
