import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { getCurrentUser } from "../../../features/auth/api";
import { LoadingScreen } from "../feedback/LoadingScreen";
import { useAuth } from "../../hooks/useAuth";

export function ProtectedRoute({ children }) {
  const location = useLocation();
  const { token, user, isAuthenticated, setUser, logout } = useAuth();

  const userQuery = useQuery({
    queryKey: ["auth", "me"],
    queryFn: getCurrentUser,
    enabled: Boolean(token && !user),
    retry: false,
  });

  useEffect(() => {
    if (userQuery.isSuccess && userQuery.data && !user) {
      setUser(userQuery.data);
    }
  }, [setUser, user, userQuery.data, userQuery.isSuccess]);

  if (!token || !isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (userQuery.isError) {
    logout({ redirect: false });
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (!user && userQuery.isLoading) {
    return <LoadingScreen label="Validando sesion" />;
  }

  return children;
}
