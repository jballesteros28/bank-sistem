import { useAuthStore } from "../../features/auth/store";

export function useAuth() {
  const token = useAuthStore((state) => state.token);
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const loginSuccess = useAuthStore((state) => state.loginSuccess);
  const setUser = useAuthStore((state) => state.setUser);
  const logout = useAuthStore((state) => state.logout);
  const hydrateFromStorage = useAuthStore((state) => state.hydrateFromStorage);

  return {
    token,
    user,
    isAuthenticated,
    loginSuccess,
    setUser,
    logout,
    hydrateFromStorage,
  };
}
