"""Export the API contract without starting a server."""

import json
from pathlib import Path

from filingguard.api.contracts import contract_definitions
from filingguard.main import create_app


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    destination = root / "contracts" / "openapi.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    schema = create_app().openapi()
    schema.setdefault("components", {}).setdefault("schemas", {}).update(contract_definitions())
    schema["x-filingguard-contract-status"] = (
        "Domain contracts defined; only paths listed here are implemented endpoints."
    )
    destination.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {destination}")


if __name__ == "__main__":
    main()
