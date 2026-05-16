import { create } from "zustand";

import {
  clearAuthStorage,
  getStoredToken,
  getStoredUser,
  removeStoredToken,
  removeStoredUser,
  setStoredToken,
  setStoredUser,
} from "../../shared/utils/storage";

const initialToken = getStoredToken();
const initialUser = getStoredUser();

export const useAuthStore = create((set) => ({
  token: initialToken,
  user: initialUser,
  isAuthenticated: Boolean(initialToken),
  loginSuccess: (token, user) => {
    // TODO: migrar el token a cookies HttpOnly en produccion.
    setStoredToken(token);
    if (user) {
      setStoredUser(user);
    }
    set({ token, user: user || null, isAuthenticated: true });
  },
  setUser: (user) => {
    if (user) {
      setStoredUser(user);
    } else {
      removeStoredUser();
    }
    set({ user });
  },
  logout: ({ redirect = true } = {}) => {
    clearAuthStorage();
    set({ token: null, user: null, isAuthenticated: false });
    if (redirect && window.location.pathname !== "/login") {
      window.location.assign("/login");
    }
  },
  hydrateFromStorage: () => {
    const token = getStoredToken();
    const user = getStoredUser();
    set({ token, user, isAuthenticated: Boolean(token) });
  },
  clearSessionOnly: () => {
    removeStoredToken();
    removeStoredUser();
    set({ token: null, user: null, isAuthenticated: false });
  },
}));
