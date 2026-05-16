import { createBrowserRouter, Navigate } from "react-router-dom";

import { AppLayout } from "../shared/components/layout/AppLayout";
import { AuthLayout } from "../shared/components/layout/AuthLayout";
import { ProtectedRoute } from "../shared/components/layout/ProtectedRoute";
import { useAuthStore } from "../features/auth/store";
import { LoginPage } from "../features/auth/pages/LoginPage";
import { OnboardingPage } from "../features/onboarding/pages/OnboardingPage";
import { DashboardPage } from "../features/dashboard/pages/DashboardPage";
import { WalletsPage } from "../features/wallets/pages/WalletsPage";
import { MovimientosPage } from "../features/movimientos/pages/MovimientosPage";
import { NotificacionesPage } from "../features/notificaciones/pages/NotificacionesPage";
import { BrandingPage } from "../features/organizacion/pages/BrandingPage";
import { PlanesPage } from "../features/planes/pages/PlanesPage";
import { IntegracionesPage } from "../features/integraciones/pages/IntegracionesPage";

function RootRedirect() {
  const isAuthenticated = useAuthStore.getState().isAuthenticated;
  return <Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />;
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <RootRedirect />,
  },
  {
    element: <AuthLayout />,
    children: [
      { path: "/login", element: <LoginPage /> },
      { path: "/onboarding", element: <OnboardingPage /> },
    ],
  },
  {
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      { path: "/dashboard", element: <DashboardPage /> },
      { path: "/wallets", element: <WalletsPage /> },
      { path: "/movimientos", element: <MovimientosPage /> },
      { path: "/notificaciones", element: <NotificacionesPage /> },
      { path: "/branding", element: <BrandingPage /> },
      { path: "/planes", element: <PlanesPage /> },
      { path: "/integraciones", element: <IntegracionesPage /> },
    ],
  },
  {
    path: "*",
    element: <Navigate to="/" replace />,
  },
]);
