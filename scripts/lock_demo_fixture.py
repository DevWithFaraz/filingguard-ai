"""Generate exact-span expectation drafts and content hashes, never human approval."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "data/demo/curated-v1"


def read_text(path):
    return path.read_bytes().decode("utf-8")


def span(text, needle):
    start = text.index(needle)
    return {"start": start, "end": start + len(needle), "text": needle}


def main():
    filing = read_text(ROOT / "filing.txt")
    sources = json.loads(read_text(ROOT / "sources.json"))["sources"]
    by_id = {source["authority_id"]: read_text(ROOT / source["path"]) for source in sources}
    scenarios = json.loads(read_text(ROOT / "scenarios.json"))
    cases = []
    for scenario in scenarios["cases"]:
        item = dict(scenario)
        item["filing_span"] = span(filing, item.pop("filing_text"))
        source_text = item.pop("source_text", None)
        item["source_span"] = (
            {"authority_id": item["authority_id"], **span(by_id[item["authority_id"]], source_text)}
            if source_text else None
        )
        cases.append(item)
    expectations = {**scenarios, "cases": cases, "reviewer": None, "reviewed_at": None}
    manifest = {
        "fixture_id": "curated-v1", "version": 1, "mode": "cached_public",
        "validation_status": "awaiting_human_review", "is_real_filing": False,
        "filing_path": "filing.txt", "pdf_path": "filing.pdf",
        "document_sha256": hashlib.sha256(filing.encode("utf-8")).hexdigest(),
        "sources_path": "sources.json", "expected_path": "expectations.json",
        "court_profile_id": "synthetic-demo-v1", "default_ai_used": True,
        "attribution": (
            "Original fictional filing paired with cached public US judicial opinions "
            "from CourtListener / Free Law Project."
        ),
        "limitations": [
            "No engine results or human-reviewed semantic ground truth yet.",
            "Combined opinion snapshots include dissents; use majority passages, "
            "not arbitrary matches.",
            "Text spans refer to original UTF-8-decoded Unicode code points; "
            "PDF spans have separate extraction mapping.",
            "Synthetic court profile is planned, not a verified real court rule.",
            "The current singular-authority demo loader does not admit "
            "this multi-authority fixture.",
        ],
    }
    for name, value in (("expectations.json", expectations), ("manifest.json", manifest)):
        content = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
        (ROOT / name).write_bytes(content.encode("utf-8"))
    print(f"Locked {len(cases)} draft scenarios; human review still required")


if __name__ == "__main__":
    main()
