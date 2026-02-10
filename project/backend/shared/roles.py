ROLE_ADMIN = "ADMIN"
ROLE_MANAGER = "MANAGER"
ROLE_OPERATOR = "OPERATOR"
ROLE_RECEIVER = "RECEIVER"
ROLE_AGENT = "AGENT"
ROLE_WMS = "WMS"
ROLE_CASHIER = "CASHIER"
ROLE_ACCOUNTANT = "ACCOUNTANT"
ROLE_CORPORATE = "CORPORATE"
ROLE_INDIVIDUAL = "INDIVIDUAL"

STAFF_ROLES = {ROLE_ADMIN, ROLE_MANAGER, ROLE_OPERATOR, ROLE_RECEIVER, ROLE_AGENT, ROLE_WMS, ROLE_CASHIER, ROLE_ACCOUNTANT}
CLIENT_ROLES = {ROLE_CORPORATE, ROLE_INDIVIDUAL}


def normalize_roles(roles: list[str] | str) -> list[str]:
    if isinstance(roles, str):
        raw = [r.strip() for r in roles.split(",") if r.strip()]
    else:
        raw = [r.strip() for r in roles if r and r.strip()]
    return [r.upper() for r in raw]


def roles_to_string(roles: list[str]) -> str:
    return ",".join(normalize_roles(roles))
