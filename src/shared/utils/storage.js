import { AUTH_TOKEN_KEY, AUTH_USER_KEY } from "./constants";

function getLocalStorage() {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage;
}

export function getToken() {
  const storage = getLocalStorage();
  if (!storage) {
    return null;
  }
  return storage.getItem(AUTH_TOKEN_KEY);
}

export function setToken(token) {
  const storage = getLocalStorage();
  if (!storage) {
    return;
  }
  storage.setItem(AUTH_TOKEN_KEY, token);
}

export function removeToken() {
  const storage = getLocalStorage();
  if (!storage) {
    return;
  }
  storage.removeItem(AUTH_TOKEN_KEY);
}

export function getUser() {
  const storage = getLocalStorage();
  if (!storage) {
    return null;
  }
  const raw = storage.getItem(AUTH_USER_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw);
  } catch {
    storage.removeItem(AUTH_USER_KEY);
    return null;
  }
}

export function setUser(user) {
  const storage = getLocalStorage();
  if (!storage) {
    return;
  }
  storage.setItem(AUTH_USER_KEY, JSON.stringify(user));
}

export function removeUser() {
  const storage = getLocalStorage();
  if (!storage) {
    return;
  }
  storage.removeItem(AUTH_USER_KEY);
}

export function clearAuthStorage() {
  removeToken();
  removeUser();
}

export const getStoredToken = getToken;
export const setStoredToken = setToken;
export const removeStoredToken = removeToken;
export const getStoredUser = getUser;
export const setStoredUser = setUser;
export const removeStoredUser = removeUser;
