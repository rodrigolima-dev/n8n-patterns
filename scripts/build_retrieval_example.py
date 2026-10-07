"""Generate the importable JSON from the tested n8n Code node source."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "tenant_retrieval.js"
OUTPUT = ROOT / "examples" / "retrieve-tenant-sample.json"


def set_assignment(item_id: str, name: str, value: str) -> dict:
    return {"id": item_id, "name": name, "value": value, "type": "string"}


def workflow() -> dict:
    return {
        "id": "c081aa66d6425c41",
        "name": "Retrieve a tenant-scoped synthetic document",
        "description": "Manual offline fixture: a Code node filters synthetic documents by tenant and publication state before deterministic keyword scoring. No database, vector store, or external service is called.",
        "active": False,
        "nodes": [
            {
                "id": "3cb87d90-728b-5fe8-ae88-3617ca0ac4f4",
                "name": "Start manually",
                "type": "n8n-nodes-base.manualTrigger",
                "typeVersion": 1,
                "position": [220, 240],
                "parameters": {},
            },
            {
                "id": "c89e1771-b965-5b38-a8e8-29d483c2db46",
                "name": "Create sample query",
                "type": "n8n-nodes-base.set",
                "typeVersion": 3.4,
                "position": [440, 240],
                "parameters": {
                    "assignments": {
                        "assignments": [
                            set_assignment("f621b338-c2ca-5bbd-aea8-c38f3b449a8c", "tenant_id", "demo-a"),
                            set_assignment("5ff2c439-25bb-592b-b3bb-a031f14fb049", "query", "shipping policy"),
                        ]
                    },
                    "options": {},
                },
            },
            {
                "id": "0c96cfd1-9176-50d2-9101-10a1fc94f700",
                "name": "Filter and rank sample documents",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [660, 240],
                "parameters": {"jsCode": SOURCE.read_text(encoding="utf-8")},
            },
        ],
        "connections": {
            "Start manually": {"main": [[{"node": "Create sample query", "type": "main", "index": 0}]]},
            "Create sample query": {"main": [[{"node": "Filter and rank sample documents", "type": "main", "index": 0}]]},
        },
        "settings": {"executionOrder": "v1"},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if the committed JSON differs from the source")
    args = parser.parse_args()
    expected = json.dumps(workflow(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != expected:
            print("FAIL: generated workflow is stale")
            return 1
        print("PASS: generated workflow matches source")
        return 0
    OUTPUT.write_text(expected, encoding="utf-8")
    print(f"Wrote {OUTPUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
