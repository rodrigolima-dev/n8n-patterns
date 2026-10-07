"""Check the structure and publication boundary of synthetic examples."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
ALLOWED_WORKFLOW_KEYS = {"id", "name", "description", "active", "nodes", "connections", "settings"}
ALLOWED_NODE_KEYS = {"id", "name", "type", "typeVersion", "position", "parameters"}
ALLOWED_TYPES = {
    "n8n-nodes-base.manualTrigger",
    "n8n-nodes-base.set",
    "n8n-nodes-base.if",
    "n8n-nodes-base.code",
}
ADDRESS = re.compile(
    r"(?:[a-z][a-z0-9+.-]*://|www\.|[\w.+-]+@[\w.-]+\.[a-z]{2,}|(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d))",
    re.I,
)
SENSITIVE_KEYS = {"credentials", "webhookid", "apikey", "api_key", "token", "password", "secret", "url", "host"}
AUTHORED_PROMPT_KEYS = {"systemmessage", "instructions"}
SECRET_MARKER = re.compile(
    r"(?:authorization|bearer|api[_-]?key|access[_-]?token|client[_-]?secret|password|private[_-]?key)",
    re.I,
)


def nested_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return {str(key).lower() for key in value} | set().union(
            *(nested_keys(child) for child in value.values())
        )
    if isinstance(value, list):
        return set().union(*(nested_keys(child) for child in value))
    return set()


def nested_strings(value: object) -> list[str]:
    if isinstance(value, dict):
        return [string for child in value.values() for string in nested_strings(child)]
    if isinstance(value, list):
        return [string for child in value for string in nested_strings(child)]
    return [value] if isinstance(value, str) else []


def validate_data(data: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["workflow must be a JSON object"]
    if set(data) - ALLOWED_WORKFLOW_KEYS:
        errors.append("unexpected workflow metadata")
    if data.get("active") is not False:
        errors.append("workflow must be inactive")

    nodes = data.get("nodes")
    connections = data.get("connections")
    if not isinstance(nodes, list) or not nodes:
        return errors + ["nodes must be a nonempty list"]
    if not isinstance(connections, dict):
        return errors + ["connections must be an object"]
    if not all(isinstance(node, dict) for node in nodes):
        return errors + ["each node must be an object"]
    if any(set(node) - ALLOWED_NODE_KEYS for node in nodes):
        errors.append("unexpected node metadata")

    names = [node.get("name") for node in nodes]
    ids = [node.get("id") for node in nodes]
    if any(not isinstance(value, str) or not value for value in names + ids):
        return errors + ["nodes require nonempty names and IDs"]
    if len(names) != len(set(names)) or len(ids) != len(set(ids)):
        errors.append("node names and IDs must be unique")
    if sum(node.get("type") == "n8n-nodes-base.manualTrigger" for node in nodes) != 1:
        errors.append("exactly one manual trigger is required")
    if any(node.get("type") not in ALLOWED_TYPES for node in nodes):
        errors.append("unexpected node type")
    trusted_code = (ROOT / "src" / "tenant_retrieval.js").read_text(encoding="utf-8")
    for node in nodes:
        if node.get("type") == "n8n-nodes-base.code" and node.get("parameters", {}).get("jsCode") != trusted_code:
            errors.append("unreviewed Code node content")
    if any(key in SENSITIVE_KEYS for key in nested_keys(data)):
        errors.append("credential or external-address field")
    if any("prompt" in key or key in AUTHORED_PROMPT_KEYS for key in nested_keys(data)):
        errors.append("prompt field")
    if any(SECRET_MARKER.search(value) for node in nodes for value in nested_strings(node.get("parameters", {}))):
        errors.append("credential-like parameter name or value")
    if ADDRESS.search(json.dumps(data, ensure_ascii=False)):
        errors.append("external address or email")

    known = set(names)
    adjacency: dict[str, set[str]] = {name: set() for name in known}
    for source, connection in connections.items():
        if source not in known or not isinstance(connection, dict):
            errors.append("connection source is invalid")
            continue
        for channel, outputs in connection.items():
            if channel != "main":
                errors.append("unexpected connection channel")
                continue
            if not isinstance(outputs, list):
                errors.append("connection outputs must be a list")
                continue
            for output in outputs:
                if not isinstance(output, list):
                    errors.append("each output must be a list")
                    continue
                for edge in output:
                    if not isinstance(edge, dict) or edge.get("node") not in known:
                        errors.append("connection target is invalid")
                    elif edge.get("type") != "main" or edge.get("index") != 0:
                        errors.append("unexpected connection channel")
                    else:
                        adjacency[source].add(edge["node"])

    for node in nodes:
        if node.get("type") == "n8n-nodes-base.if":
            outputs = connections.get(node.get("name"), {}).get("main", [])
            if len(outputs) != 2 or any(not branch for branch in outputs):
                errors.append("if node requires both outcomes")

    triggers = [node["name"] for node in nodes if node.get("type") == "n8n-nodes-base.manualTrigger"]
    if triggers:
        visited: set[str] = set()
        pending = [triggers[0]]
        while pending:
            current = pending.pop()
            if current not in visited:
                visited.add(current)
                pending.extend(adjacency.get(current, set()) - visited)
        if visited != known:
            errors.append("all main nodes must be reachable from the manual trigger")
    return errors


def main() -> int:
    paths = sorted(EXAMPLES.glob("*.json"))
    if not paths:
        print("FAIL: no examples found")
        return 1
    failures = 0
    for path in paths:
        try:
            errors = validate_data(json.loads(path.read_text(encoding="utf-8")))
        except (ValueError, UnicodeError) as exc:
            errors = [f"invalid JSON: {exc}"]
        if errors:
            failures += 1
            print(f"FAIL {path.name}: {'; '.join(errors)}")
        else:
            print(f"PASS {path.name}")
    print(f"{len(paths) - failures}/{len(paths)} examples passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
