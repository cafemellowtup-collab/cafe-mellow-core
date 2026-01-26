"""
TITAN User & Rights: JSON-based user DB (titan_users.json).
Fields: username (fixed), phone (10-digit), email, password, pin, role_tag, permissions.
Admins can edit everything except username; can delete users.
"""
import json
import os
import re

USERS_FILE = "titan_users.json"
DEFAULT_ROLES = {
    "Admin": ["dashboard", "chat", "users", "api_config", "evolution_lab"],
    "Manager": ["dashboard", "chat", "api_config", "evolution_lab"],
    "Staff": ["dashboard", "chat"],
}
TAB_KEYS = ["dashboard", "chat", "users", "api_config", "evolution_lab"]
TAB_TO_KEY = {
    "Executive Dashboard": "dashboard",
    "Intelligence Chat": "chat",
    "User & Rights": "users",
    "API & Config Center": "api_config",
    "Evolution Lab": "evolution_lab",
}


def _path():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), USERS_FILE)


def _load():
    p = _path()
    if not os.path.exists(p):
        return {"users": [], "roles": dict(DEFAULT_ROLES)}
    try:
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        if "users" not in d:
            d["users"] = []
        if "roles" not in d:
            d["roles"] = dict(DEFAULT_ROLES)
        # Migrate old format (email, role) -> (username=email, phone, pin, permissions, role_tag)
        for u in d["users"]:
            if "username" not in u and u.get("email"):
                u["username"] = u["email"]
            u.setdefault("phone", "0000000000")
            u.setdefault("pin", "")
            u.setdefault("permissions", [])
            u.setdefault("role_tag", u.get("role", "Staff"))
        return d
    except Exception:
        return {"users": [], "roles": dict(DEFAULT_ROLES)}


def _save(data):
    os.makedirs(os.path.dirname(_path()) or ".", exist_ok=True)
    with open(_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _validate_phone(phone):
    if not phone or not isinstance(phone, str):
        return False
    return bool(re.match(r"^[0-9]{10}$", re.sub(r"\s", "", phone)))


def get_roles():
    return _load().get("roles", DEFAULT_ROLES)


def get_tab_access(role: str, user_dict=None):
    """If user_dict has non-empty permissions, use that; else use role's default tabs."""
    if user_dict and (user_dict.get("permissions") or []) != []:
        return [t for t in (user_dict.get("permissions") or []) if t in TAB_KEYS]
    roles = get_roles()
    return roles.get(role, roles.get("Staff", ["dashboard", "chat"]))


def can_access_tab(role: str, tab_key: str, user_dict=None) -> bool:
    return tab_key in get_tab_access(role, user_dict)


def get_users():
    return _load().get("users", [])


def get_user_by_username(username: str):
    if not username:
        return None
    u = (username or "").strip()
    for x in get_users():
        if (x.get("username") or "").strip() == u:
            return x
    return None


def add_user(username, phone, email, password, pin, role_tag, permissions=None):
    username = (username or "").strip()
    if not username:
        raise ValueError("Username is required.")
    if get_user_by_username(username):
        raise ValueError(f"Username '{username}' already exists.")
    if not _validate_phone(phone):
        raise ValueError("Phone must be 10 digits.")
    d = _load()
    perms = [p for p in (permissions or []) if p in TAB_KEYS]
    d["users"].append({
        "username": username,
        "phone": str(phone or "").strip(),
        "email": str(email or "").strip(),
        "password": str(password or ""),
        "pin": str(pin or "").strip(),
        "role_tag": str(role_tag or "Staff").strip(),
        "permissions": perms,
    })
    _save(d)


def update_user(username, **kwargs):
    username = (username or "").strip()
    if not username:
        raise ValueError("Username is required.")
    d = _load()
    for u in d["users"]:
        if (u.get("username") or "").strip() == username:
            # Never allow changing username
            for k, v in kwargs.items():
                if k == "username":
                    continue
                if k == "phone" and not _validate_phone(v):
                    raise ValueError("Phone must be 10 digits.")
                if k == "permissions":
                    u[k] = [p for p in (v or []) if p in TAB_KEYS]
                elif k in ("phone", "email", "password", "pin", "role_tag"):
                    u[k] = str(v or "").strip() if k != "password" else str(v or "")
            _save(d)
            return
    raise ValueError(f"User '{username}' not found.")


def delete_user(username: str):
    username = (username or "").strip()
    if not username:
        raise ValueError("Username is required.")
    d = _load()
    before = len(d["users"])
    d["users"] = [u for u in d["users"] if (u.get("username") or "").strip() != username]
    if len(d["users"]) == before:
        raise ValueError(f"User '{username}' not found.")
    _save(d)


def set_user(email: str, role: str, **kw):
    """Legacy: add/update by email as username. Prefer add_user/update_user."""
    email = (email or "").strip()
    if not email:
        raise ValueError("Email is required.")
    existing = get_user_by_username(email)
    if existing:
        update_user(email, role_tag=role, **kw)
    else:
        add_user(username=email, phone=kw.get("phone", "0000000000"), email=email, password=kw.get("password", ""), pin=kw.get("pin", ""), role_tag=role, permissions=kw.get("permissions"))
