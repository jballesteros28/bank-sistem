import { AUTH_TOKEN_KEY, AUTH_USER_KEY } from "./constants";

export function getStoredToken() {
  return window.localStorage.getItem(AUTH_TOKEN_KEY);
}

export function setStoredToken(token) {
  window.localStorage.setItem(AUTH_TOKEN_KEY, token);
}

export function removeStoredToken() {
  window.localStorage.removeItem(AUTH_TOKEN_KEY);
}

export function getStoredUser() {
  const raw = window.localStorage.getItem(AUTH_USER_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw);
  } catch {
    window.localStorage.removeItem(AUTH_USER_KEY);
    return null;
  }
}

export function setStoredUser(user) {
  window.localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
}

export function removeStoredUser() {
  window.localStorage.removeItem(AUTH_USER_KEY);
}

export function clearAuthStorage() {
  removeStoredToken();
  removeStoredUser();
}
