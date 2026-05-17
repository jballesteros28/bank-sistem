import { ROLES } from "./constants";

function getRole(user) {
  return user?.rol || user?.role || "";
}

function isSameUser(user, targetUser) {
  return Boolean(user?.id && targetUser?.id && user.id === targetUser.id);
}

function isSameOrganization(user, targetUser) {
  if (!user?.organizacion_id || !targetUser?.organizacion_id) {
    return true;
  }
  return user.organizacion_id === targetUser.organizacion_id;
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

export function canCreateFinancialMovement(user) {
  return isOwner(user) || isAdmin(user) || isSuperAdmin(user);
}

export function canCreateClientPayment(user) {
  return isClient(user);
}

export function canReverseMovement(user) {
  return canCreateFinancialMovement(user);
}

export function canViewMovements(user) {
  return Boolean(getRole(user));
}

export function canViewOrganizationNotifications(user) {
  return isOwner(user) || isAdmin(user) || isSuperAdmin(user);
}

export function canEditBranding(user) {
  return isOwner(user) || isAdmin(user) || isSuperAdmin(user);
}

export function canViewBranding(user) {
  return canEditBranding(user) || isSupport(user);
}

export function canViewPlans(user) {
  return canEditBranding(user) || isSupport(user);
}

export function canViewCurrentPlan(user) {
  return canEditBranding(user);
}

export function canManageApiKeys(user) {
  return isOwner(user) || isAdmin(user) || isSuperAdmin(user);
}

export function canManageWebhooks(user, planAllowsWebhooks = true) {
  return Boolean(planAllowsWebhooks) && (isOwner(user) || isAdmin(user) || isSuperAdmin(user));
}

export function canViewWebhookDeliveries(user) {
  return isOwner(user) || isAdmin(user) || isSuperAdmin(user) || isSupport(user);
}

export function canViewDeveloperPortal(user) {
  return isOwner(user) || isAdmin(user) || isSuperAdmin(user) || isSupport(user);
}

export function canViewRewards(user) {
  return isOwner(user) || isAdmin(user) || isSuperAdmin(user) || isSupport(user) || isClient(user);
}

export function canManageRewardRules(user) {
  return isOwner(user) || isAdmin(user) || isSuperAdmin(user);
}

export function canApplyRewards(user) {
  return isOwner(user) || isAdmin(user) || isSuperAdmin(user);
}

export function canSimulateRewards(user) {
  return isOwner(user) || isAdmin(user) || isSuperAdmin(user) || isSupport(user);
}

export function canViewRewardApplications(user) {
  return isOwner(user) || isAdmin(user) || isSuperAdmin(user) || isSupport(user) || isClient(user);
}

export function canViewUsers(user) {
  return isOwner(user) || isAdmin(user) || isSuperAdmin(user);
}

export function canCreateUsers(user) {
  if (isSuperAdmin(user)) {
    return Boolean(user?.organizacion_id);
  }
  return (isOwner(user) || isAdmin(user)) && Boolean(user?.organizacion_id);
}

export function canChangeUserRole(user, targetUser) {
  if (!canViewUsers(user) || !targetUser || isSameUser(user, targetUser) || !isSameOrganization(user, targetUser)) {
    return false;
  }
  if (isSuperAdmin(targetUser)) {
    return false;
  }
  if (isSuperAdmin(user) || isOwner(user)) {
    return true;
  }
  return isAdmin(user) && !isOwner(targetUser);
}

export function canChangeUserStatus(user, targetUser) {
  if (!canViewUsers(user) || !targetUser || isSameUser(user, targetUser) || !isSameOrganization(user, targetUser)) {
    return false;
  }
  if (isSuperAdmin(targetUser)) {
    return false;
  }
  if (isSuperAdmin(user) || isOwner(user)) {
    return true;
  }
  return isAdmin(user) && !isOwner(targetUser);
}
