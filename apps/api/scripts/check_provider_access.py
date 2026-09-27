"""Explicit live checks; print metadata only, never credentials or response bodies."""

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[3]
COURT = "https://www.courtlistener.com/api/rest/v4/"


def credential(name: str) -> str:
    # Prefer the backend file; support the root file without copying secrets.
    for location in (ROOT / "apps/api/.env", ROOT / ".env"):
        value = dotenv_values(location).get(name)
        if value and value.strip():
            return value.strip()
    raise ValueError(f"Missing {name}; set it in apps/api/.env")


def request(client: httpx.Client, method: str, url: str, **kwargs) -> httpx.Response:
    response = client.request(method, url, **kwargs)
    print(json.dumps({"endpoint": url, "http_status": response.status_code}))
    response.raise_for_status()
    return response


def courtlistener() -> None:
    token = credential("COURTLISTENER_API_TOKEN")
    with httpx.Client(
        headers={"Authorization": f"Token {token}", "Accept": "application/json"},
        timeout=20, follow_redirects=False,
    ) as client:
        usage = request(client, "GET", COURT + "api-usage/").json()
        fields = ("scope", "rate", "limit", "remaining", "blocked")
        print(json.dumps({"quotas": [
            {key: item.get(key) for key in fields}
            for item in usage.get("current_usage", [])
        ]}))
        lookup = request(
            client, "POST", COURT + "citation-lookup/", data={"text": "576 U.S. 644"},
        ).json()
        if not isinstance(lookup, list) or len(lookup) != 1:
            raise ValueError("Unexpected lookup shape; no verification claimed")
        result = lookup[0]
        clusters = result.get("clusters", [])
        print(json.dumps({
            "citation": "576 U.S. 644", "lookup_status": result.get("status"),
            "cluster_count": len(clusters),
        }))
        if result.get("status") != 200 or len(clusters) != 1:
            raise ValueError("Lookup was not an unambiguous match")
        opinions = clusters[0].get("sub_opinions", [])
        if not opinions:
            raise ValueError("Matched authority has no opinion references")
        reference = opinions[0]
        if isinstance(reference, int):
            opinion_id = reference
        elif isinstance(reference, str):
            parsed = urlparse(reference)
            if parsed.netloc != "www.courtlistener.com":
                raise ValueError("Opinion URL has an unapproved host")
            opinion_id = int(parsed.path.rstrip("/").split("/")[-1])
        else:
            raise ValueError("Unexpected opinion reference")
        opinion_url = COURT + f"opinions/{opinion_id}/"
        opinion = request(client, "GET", opinion_url).json()
        text_field = next((
            key for key in ("plain_text", "html_with_citations", "html", "html_lawbox",
                            "html_columbia", "xml_harvard")
            if isinstance(opinion.get(key), str) and opinion[key].strip()
        ), None)
        if text_field is None:
            raise ValueError("Opinion retrieved but source text unavailable")
        text = opinion[text_field]
        print(json.dumps({
            "opinion_id": opinion_id, "cluster_id": clusters[0].get("id"),
            "text_field": text_field, "characters": len(text),
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
            "source_url": opinion_url, "checked_at": datetime.now(UTC).isoformat(),
        }))


def groq_models() -> None:
    key = credential("GROQ_API_KEY")
    with httpx.Client(
        headers={"Authorization": f"Bearer {key}"}, timeout=20, follow_redirects=False,
    ) as client:
        payload = request(client, "GET", "https://api.groq.com/openai/v1/models").json()
        models = sorted(item["id"] for item in payload["data"] if item.get("active", True))
        print(json.dumps({"active_model_ids": models}))
        print("Listing models confirms authentication, not free-tier inference or quality.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("provider", choices=("courtlistener", "groq"))
    args = parser.parse_args()
    try:
        (courtlistener if args.provider == "courtlistener" else groq_models)()
    except httpx.HTTPStatusError as error:
        print(json.dumps({"error": "provider_http_error", "status": error.response.status_code}))
        return 1
    except httpx.RequestError as error:
        print(json.dumps({"error": "provider_transport_error", "kind": type(error).__name__}))
        return 1
    except (ValueError, KeyError, TypeError) as error:
        # Only our fixed validation messages are exposed; parser errors remain opaque.
        print(json.dumps({"error": "configuration_or_payload_error", "kind": type(error).__name__}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
