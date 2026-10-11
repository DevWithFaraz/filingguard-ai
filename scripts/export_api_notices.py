import json
from importlib import metadata
from pathlib import Path

rows = []
text = [
    "FilingGuard API installed dependency license evidence",
    "Includes development/probe tools; generated from this locked local environment, "
    "not a legal clearance certificate.",
]
for dist in sorted(metadata.distributions(), key=lambda d: d.metadata["Name"].lower()):
    name = dist.metadata["Name"]
    if name == "filingguard-api":
        continue
    files = [
        f
        for f in dist.files or []
        if f.name.lower().startswith(("license", "licence", "copying", "notice"))
        and dist.locate_file(f).is_file()
    ]
    license_name = (
        dist.metadata.get("License-Expression") or dist.metadata.get("License") or "UNDECLARED"
    )
    source = dist.metadata.get_all("Project-URL") or [dist.metadata.get("Home-page", "")]
    rows.append(
        {
            "package": name,
            "version": dist.version,
            "license": license_name,
            "files": [str(f) for f in files],
            "source": source,
        }
    )
    text.extend(
        [
            "=" * 72,
            name + "@" + dist.version,
            "Declared license: " + license_name,
            "Source: " + "; ".join(source),
        ]
    )
    if not files:
        text.append(
            "No separate license file in installed distribution; consult upstream metadata/source."
        )
    for file in files:
        text.extend(
            [str(file), dist.locate_file(file).read_text(encoding="utf8", errors="replace")]
        )
root = Path(__file__).resolve().parents[1]
(root / "docs/delivery/api-dependency-notices.txt").write_text("\n".join(text), encoding="utf8")
(root / ".runtime/t059").mkdir(parents=True, exist_ok=True)
(root / ".runtime/t059/python-license-inventory.json").write_text(
    json.dumps(rows, indent=2), encoding="utf8"
)
print(
    json.dumps(
        {
            "packages": len(rows),
            "missingLicenseFiles": [r["package"] for r in rows if not r["files"]],
        }
    )
)
