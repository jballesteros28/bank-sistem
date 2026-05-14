// src/routes/ProtectedRoute.jsx
import { Navigate } from "react-router-dom";
import { useAuthCtx } from "../hooks/useAuthCtx";

export default function ProtectedRoute({ children }) {
  const { user } = useAuthCtx();
  const token = localStorage.getItem("bank.jwt");

  // 🚫 Si no hay sesión activa, redirige al login
  if (!user && !token) {
    return <Navigate to="/auth/login" replace />;
  }

  // ✅ Si hay sesión, renderiza el contenido protegido
  return children;
}
