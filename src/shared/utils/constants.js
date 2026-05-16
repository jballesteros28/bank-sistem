export const APP_NAME = import.meta.env.VITE_APP_NAME || "Wallet SaaS";

export const AUTH_TOKEN_KEY = "wallet_saas_token";
export const AUTH_USER_KEY = "wallet_saas_user";

export const ROLES = {
  superAdmin: "super_admin",
  owner: "owner",
  admin: "admin",
  soporte: "soporte",
  cliente: "cliente",
};

export const ROUTES = {
  login: "/login",
  onboarding: "/onboarding",
  dashboard: "/dashboard",
  wallets: "/wallets",
  movimientos: "/movimientos",
  notificaciones: "/notificaciones",
  branding: "/branding",
  planes: "/planes",
  integraciones: "/integraciones",
  usuarios: "/usuarios",
};
