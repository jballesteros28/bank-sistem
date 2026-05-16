import { useAuthStore } from "../../features/auth/store";

export function useAuth() {
  const token = useAuthStore((state) => state.token);
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isHydrated = useAuthStore((state) => state.isHydrated);
  const loginSuccess = useAuthStore((state) => state.loginSuccess);
  const setUser = useAuthStore((state) => state.setUser);
  const updateUser = useAuthStore((state) => state.updateUser);
  const logout = useAuthStore((state) => state.logout);
  const hydrateFromStorage = useAuthStore((state) => state.hydrateFromStorage);

  return {
    token,
    user,
    isAuthenticated,
    isHydrated,
    loginSuccess,
    setUser,
    updateUser,
    logout,
    hydrateFromStorage,
  };
}
