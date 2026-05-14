// src/routes/AppRouter.jsx
import { Routes, Route, Navigate } from "react-router-dom";
import ProtectedRoute from "./ProtectedRoute";

// Auth
import Login from "../pages/auth/Login";
import Register from "../pages/auth/Register";
import ResetPassword from "../pages/auth/ResetPassword";

// Dashboard / Admin
import DashboardAdmin from "../pages/admin/DashboardAdmin";
import UsuariosAdmin from "../pages/admin/UsuariosAdmin";
import ReportesAdmin from "../pages/admin/ReportesAdmin";

// Cuentas
import CuentasList from "../pages/cuentas/CuentasList";
import CuentaDetalle from "../pages/cuentas/CuentaDetalle";
import CrearCuenta from "../pages/cuentas/CrearCuenta";

// Transacciones
import Transferir from "../pages/transacciones/Transferir";
import Historial from "../pages/transacciones/Historial";

// Notificaciones
import LogsSistema from "../pages/notificaciones/LogsSistema";
import EmailsSistema from "../pages/notificaciones/EmailsSistema";

// Usuarios
import Perfil from "../pages/usuarios/Perfil";
import Configuracion from "../pages/usuarios/Configuracion";

export default function AppRouter() {
  return (
    <Routes>
      🔓 Rutas públicas
      <Route path="/auth/login" element={<Login />} />
      <Route path="/auth/register" element={<Register />} />
      <Route path="/auth/reset-password" element={<ResetPassword />} />

      {/* 🔒 Rutas protegidas */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardAdmin />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/dashboard"
        element={
          <ProtectedRoute>
            <DashboardAdmin />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/usuarios"
        element={
          <ProtectedRoute>
            <UsuariosAdmin />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/reportes"
        element={
          <ProtectedRoute>
            <ReportesAdmin />
          </ProtectedRoute>
        }
      />
      <Route
        path="/cuentas/listar"
        element={
          <ProtectedRoute>
            <CuentasList />
          </ProtectedRoute>
        }
      />
      <Route
        path="/cuentas/:id"
        element={
          <ProtectedRoute>
            <CuentaDetalle />
          </ProtectedRoute>
        }
      />
      <Route
        path="/cuentas/nueva"
        element={
          <ProtectedRoute>
            <CrearCuenta />
          </ProtectedRoute>
        }
      />
      <Route
        path="/transacciones"
        element={
          <ProtectedRoute>
            <Historial />
          </ProtectedRoute>
        }
      />
      <Route
        path="/transacciones/transferir"
        element={
          <ProtectedRoute>
            <Transferir />
          </ProtectedRoute>
        }
      />
      <Route
        path="/notificaciones/logs"
        element={
          <ProtectedRoute>
            <LogsSistema />
          </ProtectedRoute>
        }
      />
      <Route
        path="/notificaciones/emails"
        element={
          <ProtectedRoute>
            <EmailsSistema />
          </ProtectedRoute>
        }
      />
      <Route
        path="/usuarios/perfil"
        element={
          <ProtectedRoute>
            <Perfil />
          </ProtectedRoute>
        }
      />
      <Route
        path="/usuarios/configuracion"
        element={
          <ProtectedRoute>
            <Configuracion />
          </ProtectedRoute>
        }
      />

      {/* 🧭 Fallback */}
      <Route path="*" element={<Navigate to="/auth/login" replace />} />
    </Routes>
  );
}
