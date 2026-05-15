from app.shared.enums import RolUsuario


ADMIN_ROLES = {RolUsuario.owner, RolUsuario.admin, RolUsuario.super_admin}
OPERADOR_ROLES = {RolUsuario.owner, RolUsuario.admin, RolUsuario.soporte, RolUsuario.super_admin}


def is_super_admin(role: RolUsuario | str) -> bool:
    return str(role) == RolUsuario.super_admin.value


def is_admin(role: RolUsuario | str) -> bool:
    return str(role) in {role.value for role in ADMIN_ROLES}


def is_operator(role: RolUsuario | str) -> bool:
    return str(role) in {role.value for role in OPERADOR_ROLES}

