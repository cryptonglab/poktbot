from poktbot.telegram.rbac.role import Role
from poktbot.telegram.rbac.composite import SysAdmin, Admin, Investor


AVAILABLE_ROLES = [
    SysAdmin,
    Admin,
    Investor
]


def get_roles(entity, conv):

    # We inject the relay DB here if not provided
    # TODO: Make relay db singleton perhaps?
    #if relay_db is None:
    #    relay_db = get_relaydb()

    roles = [rol(entity=entity, conv=conv) for rol in AVAILABLE_ROLES]

    # We filter by which roles are allowed to this entity
    roles = [rol for rol in roles if rol.allowed()]

    return roles


__all__ = ["Role", "get_roles"]
