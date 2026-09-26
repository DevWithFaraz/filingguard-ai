"""Export the API contract without starting a server."""

import json
from pathlib import Path

from filingguard.main import create_app


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    destination = root / "contracts" / "openapi.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(create_app().openapi(), indent=2) + "\n", encoding="utf-8")
    print(f"Exported {destination}")


if __name__ == "__main__":
    main()
