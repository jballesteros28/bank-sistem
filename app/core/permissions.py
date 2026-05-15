from app.shared.enums import RolUsuario


ADMIN_ROLES = {RolUsuario.owner, RolUsuario.admin, RolUsuario.super_admin}
OPERADOR_ROLES = {RolUsuario.owner, RolUsuario.admin, RolUsuario.super_admin}
FINANCIAL_OPERATOR_ROLES = OPERADOR_ROLES
CONSULTA_ROLES = FINANCIAL_OPERATOR_ROLES | {RolUsuario.soporte}


def is_super_admin(role: RolUsuario | str) -> bool:
    return str(role) == RolUsuario.super_admin.value


def is_admin(role: RolUsuario | str) -> bool:
    return str(role) in {role.value for role in ADMIN_ROLES}


def is_operator(role: RolUsuario | str) -> bool:
    return str(role) in {role.value for role in OPERADOR_ROLES}


def is_financial_operator(role: RolUsuario | str) -> bool:
    return str(role) in {role.value for role in FINANCIAL_OPERATOR_ROLES}


def can_consult_financial_info(role: RolUsuario | str) -> bool:
    return str(role) in {role.value for role in CONSULTA_ROLES}
