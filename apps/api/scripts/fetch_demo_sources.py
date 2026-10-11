"""Explicit bounded retrieval of public opinions; never persists raw API payloads."""

import argparse
import hashlib
import json
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path

import httpx
from check_provider_access import credential

ROOT = Path(__file__).resolve().parents[3]
DESTINATION = ROOT / "data/demo/curated-v1"
BASE = "https://www.courtlistener.com/api/rest/v4/"
CASES = (
    ("brown", "347 U.S. 483", "Brown v. Board of Education", 1954),
    ("miranda", "384 U.S. 436", "Miranda v. Arizona", 1966),
    ("obergefell", "576 U.S. 644", "Obergefell v. Hodges", 2015),
)


class OpinionText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1
        elif tag in {"p", "div", "br", "h1", "h2", "h3", "li"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)
        elif tag in {"p", "div", "h1", "h2", "h3", "li"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=[case[0] for case in CASES])
    args = parser.parse_args()
    manifest_path = DESTINATION / "sources.json"
    sources = json.loads(manifest_path.read_text("utf-8"))["sources"] if args.only else []
    directory = DESTINATION / "authorities"
    directory.mkdir(parents=True, exist_ok=True)
    with httpx.Client(
        headers={"Authorization": f"Token {credential('COURTLISTENER_API_TOKEN')}"},
        timeout=30,
        follow_redirects=False,
    ) as client:
        for key, citation, name, year in CASES:
            if args.only and args.only != key:
                continue
            response = client.post(BASE + "citation-lookup/", data={"text": citation})
            response.raise_for_status()
            results = response.json()
            if len(results) != 1 or results[0].get("status") != 200:
                raise ValueError("Unresolved fixture authority")
            clusters = results[0].get("clusters", [])
            if len(clusters) != 1:
                raise ValueError("Ambiguous fixture authority")
            cluster = clusters[0]
            refs = cluster.get("sub_opinions", [])
            if not refs:
                raise ValueError("No opinion reference")
            def reference_id(value):
                if isinstance(value, int):
                    return value
                if isinstance(value, str) and value.startswith(BASE + "opinions/"):
                    return int(value.rstrip("/").split("/")[-1])
                raise ValueError("Unexpected opinion reference")

            ref = min(refs, key=reference_id)
            if isinstance(ref, int):
                opinion_id = ref
            elif isinstance(ref, str) and ref.startswith(BASE + "opinions/"):
                opinion_id = int(ref.rstrip("/").split("/")[-1])
            else:
                raise ValueError("Unexpected opinion reference")
            url = BASE + f"opinions/{opinion_id}/"
            response = client.get(url)
            response.raise_for_status()
            opinion = response.json()
            if opinion.get("type") not in {"010combined", "020lead"}:
                raise ValueError("Non-majority opinion selected; source rejected")
            field = next((
                name for name in ("plain_text", "html_with_citations", "html", "html_lawbox")
                if isinstance(opinion.get(name), str) and opinion[name].strip()
            ), None)
            if field is None:
                raise ValueError("Plain text unavailable; no invented source permitted")
            raw = opinion[field]
            if field == "plain_text":
                text = raw
                method = "identity-v1"
            else:
                parsed = OpinionText()
                parsed.feed(raw)
                text = "".join(parsed.parts)
                (directory / f"{key}.html").write_bytes(raw.encode("utf-8"))
                method = "htmlparser-block-boundaries-v1"
            path = directory / f"{key}.txt"
            path.write_bytes(text.encode("utf-8"))
            sources = [source for source in sources if source["authority_id"] != key]
            sources.append({
                "authority_id": key, "citation": citation, "case_name": name,
                "year": year, "court": "Supreme Court of the United States",
                "cluster_id": cluster["id"], "opinion_id": opinion_id,
                "provider_case_name": cluster.get("case_name"),
                "provider_opinion_type": opinion.get("type"),
                "source_url": url, "text_field": field, "text_conversion": method,
                "raw_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
                "raw_path": (
                    f"authorities/{key}.html" if field != "plain_text"
                    else f"authorities/{key}.txt"
                ),
                "retrieved_at": datetime.now(UTC).isoformat(),
                "path": f"authorities/{key}.txt",
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "characters": len(text), "provenance": "cached_public",
                "attribution": (
                    "Public US judicial opinion, retrieved from CourtListener / Free Law Project"
                ),
            })
            print(json.dumps({"authority_id": key, "http_status": 200, "characters": len(text)}))
    (DESTINATION / "sources.json").write_text(
        json.dumps({"sources": sources}, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as error:
        safe_messages = {
            "Unresolved fixture authority", "Ambiguous fixture authority",
            "No opinion reference", "Unexpected opinion reference",
            "Plain text unavailable; no invented source permitted",
            "Non-majority opinion selected; source rejected",
        }
        detail = (
            str(error) if isinstance(error, ValueError) and str(error) in safe_messages else None
        )
        print(json.dumps({"error": type(error).__name__, "detail": detail}))
        raise SystemExit(1) from None
