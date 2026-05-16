import { lazy, Suspense } from "react";
import { createBrowserRouter, Navigate } from "react-router-dom";

import { AppLayout } from "../shared/components/layout/AppLayout";
import { AuthLayout } from "../shared/components/layout/AuthLayout";
import { ProtectedRoute } from "../shared/components/layout/ProtectedRoute";
import { LoadingScreen } from "../shared/components/feedback/LoadingScreen";
import { useAuthStore } from "../features/auth/store";
import { LoginPage } from "../features/auth/pages/LoginPage";
import { OnboardingPage } from "../features/onboarding/pages/OnboardingPage";

const DashboardPage = lazy(() =>
  import("../features/dashboard/pages/DashboardPage").then((module) => ({ default: module.DashboardPage })),
);
const WalletsPage = lazy(() =>
  import("../features/wallets/pages/WalletsPage").then((module) => ({ default: module.WalletsPage })),
);
const MovimientosPage = lazy(() =>
  import("../features/movimientos/pages/MovimientosPage").then((module) => ({ default: module.MovimientosPage })),
);
const NotificacionesPage = lazy(() =>
  import("../features/notificaciones/pages/NotificacionesPage").then((module) => ({ default: module.NotificacionesPage })),
);
const BrandingPage = lazy(() =>
  import("../features/organizacion/pages/BrandingPage").then((module) => ({ default: module.BrandingPage })),
);
const PlanesPage = lazy(() =>
  import("../features/planes/pages/PlanesPage").then((module) => ({ default: module.PlanesPage })),
);
const IntegracionesPage = lazy(() =>
  import("../features/integraciones/pages/IntegracionesPage").then((module) => ({ default: module.IntegracionesPage })),
);

function RootRedirect() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isHydrated = useAuthStore((state) => state.isHydrated);

  if (!isHydrated) {
    return <LoadingScreen label="Preparando sesion" />;
  }

  return <Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />;
}

function lazyRoute(Page) {
  return (
    <Suspense fallback={<LoadingScreen label="Cargando vista" />}>
      <Page />
    </Suspense>
  );
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
      { path: "/dashboard", element: lazyRoute(DashboardPage) },
      { path: "/wallets", element: lazyRoute(WalletsPage) },
      { path: "/movimientos", element: lazyRoute(MovimientosPage) },
      { path: "/notificaciones", element: lazyRoute(NotificacionesPage) },
      { path: "/branding", element: lazyRoute(BrandingPage) },
      { path: "/planes", element: lazyRoute(PlanesPage) },
      { path: "/integraciones", element: lazyRoute(IntegracionesPage) },
    ],
  },
  {
    path: "*",
    element: <Navigate to="/" replace />,
  },
]);
