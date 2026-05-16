import { useEffect } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useCurrentUser } from "../../../features/auth/hooks/useCurrentUser";
import { LoadingScreen } from "../feedback/LoadingScreen";
import { useAuth } from "../../hooks/useAuth";

export function ProtectedRoute({ children }) {
  const location = useLocation();
  const { token, user, isAuthenticated, isHydrated, setUser, logout } = useAuth();

  const userQuery = useCurrentUser({
    enabled: isHydrated && Boolean(token && !user),
  });

  useEffect(() => {
    if (userQuery.isSuccess && userQuery.data && !user) {
      setUser(userQuery.data);
    }
  }, [setUser, user, userQuery.data, userQuery.isSuccess]);

  useEffect(() => {
    if (userQuery.isError) {
      logout({ redirect: false });
    }
  }, [logout, userQuery.isError]);

  if (!isHydrated) {
    return <LoadingScreen label="Preparando sesion" />;
  }

  if (!token || !isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (userQuery.isError) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (!user) {
    return <LoadingScreen label="Validando sesion" />;
  }

  return children;
}
