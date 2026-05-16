import { ROLES } from "./constants";

function getRole(user) {
  return user?.rol || user?.role || "";
}

export function isOwner(user) {
  return getRole(user) === ROLES.owner;
}

export function isAdmin(user) {
  return getRole(user) === ROLES.admin;
}

export function isSupport(user) {
  return getRole(user) === ROLES.soporte;
}

export function isClient(user) {
  return getRole(user) === ROLES.cliente;
}

export function isSuperAdmin(user) {
  return getRole(user) === ROLES.superAdmin;
}

export function canManageOrganizationWallets(user) {
  return isOwner(user) || isAdmin(user) || isSuperAdmin(user);
}

export function canViewOrganizationWallets(user) {
  return canManageOrganizationWallets(user) || isSupport(user);
}
