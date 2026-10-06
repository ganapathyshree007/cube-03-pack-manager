"""Create a private local customer account for the existing local workspace."""

import hashlib
import json
import secrets
from pathlib import Path

from backend.integrated.api import local_guard


def main():
    local_guard()
    root = Path(".local")
    target = root / "customer-client.json"
    if target.exists():
        print("Existing local customer account preserved.")
        return
    workspace = json.loads((root / "integrated-client.json").read_text())
    users_path = root / "integrated-users.json"
    users = json.loads(users_path.read_text())
    token = secrets.token_urlsafe(32)
    users.append(
        {
            "organization": workspace["organization"],
            "operator": "local-customer",
            "role": "customer",
            "token_hash": hashlib.sha256(token.encode()).hexdigest(),
        }
    )
    with target.open("x") as f:
        json.dump({"organization": workspace["organization"], "token": token}, f)
    temp = users_path.with_suffix(".tmp")
    temp.write_text(json.dumps(users))
    temp.replace(users_path)
    print(
        "Created .local/customer-client.json. Choose this private file at /shop.html; no credentials printed."
    )


if __name__ == "__main__":
    main()
