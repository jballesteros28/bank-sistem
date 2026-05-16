import { create } from "zustand";

import {
  clearAuthStorage,
  getToken,
  getUser,
  removeToken,
  removeUser,
  setToken,
  setUser as setStoredUser,
} from "../../shared/utils/storage";

export const useAuthStore = create((set, get) => ({
  token: null,
  user: null,
  isAuthenticated: false,
  isHydrated: false,
  loginSuccess: (token, user) => {
    // TODO: migrar el token a cookies HttpOnly en produccion.
    setToken(token);
    if (user) {
      setStoredUser(user);
    } else {
      removeUser();
    }
    set({ token, user: user || null, isAuthenticated: Boolean(token), isHydrated: true });
  },
  setUser: (user) => {
    if (user) {
      setStoredUser(user);
    } else {
      removeUser();
    }
    set({ user });
  },
  updateUser: (user) => {
    const currentUser = get().user || {};
    const nextUser = user ? { ...currentUser, ...user } : null;
    if (nextUser) {
      setStoredUser(nextUser);
    } else {
      removeUser();
    }
    set({ user: nextUser });
  },
  logout: ({ redirect = true } = {}) => {
    clearAuthStorage();
    set({ token: null, user: null, isAuthenticated: false, isHydrated: true });
    if (redirect && window.location.pathname !== "/login") {
      window.location.assign("/login");
    }
  },
  hydrateFromStorage: () => {
    const token = getToken();
    const user = getUser();
    set({ token, user, isAuthenticated: Boolean(token), isHydrated: true });
  },
  clearSessionOnly: () => {
    removeToken();
    removeUser();
    set({ token: null, user: null, isAuthenticated: false, isHydrated: true });
  },
}));
