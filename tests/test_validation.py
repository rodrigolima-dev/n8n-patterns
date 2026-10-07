"""Regression tests for the public example boundary."""

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_examples import validate_data  # noqa: E402


class ExampleValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sample = json.loads((ROOT / "examples" / "validate-event-envelope.json").read_text(encoding="utf-8"))

    def test_checked_example_is_valid(self):
        self.assertEqual(validate_data(self.sample), [])

    def test_prompt_field_is_rejected(self):
        example = copy.deepcopy(self.sample)
        example["nodes"][1]["parameters"]["promptType"] = "define"
        self.assertIn("prompt field", validate_data(example))

    def test_agent_node_is_rejected(self):
        example = copy.deepcopy(self.sample)
        example["nodes"][1]["type"] = "@n8n/n8n-nodes-langchain.agent"
        self.assertIn("unexpected node type", validate_data(example))

    def test_unreviewed_code_node_is_rejected(self):
        example = json.loads((ROOT / "examples" / "retrieve-tenant-sample.json").read_text(encoding="utf-8"))
        code_node = next(node for node in example["nodes"] if node["type"] == "n8n-nodes-base.code")
        code_node["parameters"]["jsCode"] += "\nreturn [];\n"
        self.assertIn("unreviewed Code node content", validate_data(example))

    def test_activation_is_rejected(self):
        example = copy.deepcopy(self.sample)
        example["active"] = True
        self.assertIn("workflow must be inactive", validate_data(example))

    def test_pinned_execution_data_is_rejected(self):
        example = copy.deepcopy(self.sample)
        example["pinData"] = {"Create sample event": [{"json": {"private": "sample"}}]}
        self.assertIn("unexpected workflow metadata", validate_data(example))

    def test_node_notes_are_rejected(self):
        example = copy.deepcopy(self.sample)
        example["nodes"][1]["notes"] = "operational note"
        self.assertIn("unexpected node metadata", validate_data(example))

    def test_network_node_is_rejected(self):
        example = copy.deepcopy(self.sample)
        example["nodes"][1]["type"] = "n8n-nodes-base.httpRequest"
        self.assertIn("unexpected node type", validate_data(example))

    def test_credential_is_rejected(self):
        example = copy.deepcopy(self.sample)
        example["nodes"][1]["credentials"] = {"example": {"id": "placeholder"}}
        self.assertIn("credential or external-address field", validate_data(example))

    def test_inline_authorization_is_rejected(self):
        example = copy.deepcopy(self.sample)
        assignment = example["nodes"][1]["parameters"]["assignments"]["assignments"][0]
        assignment["name"] = "Authorization"
        assignment["value"] = "Bearer " + "x" * 32
        self.assertIn("credential-like parameter name or value", validate_data(example))

    def test_broken_edge_is_rejected(self):
        example = copy.deepcopy(self.sample)
        example["connections"]["Start manually"]["main"][0][0]["node"] = "Missing node"
        self.assertIn("connection target is invalid", validate_data(example))

    def test_missing_rejection_branch_is_rejected(self):
        example = copy.deepcopy(self.sample)
        example["connections"]["Check event envelope"]["main"][1] = []
        self.assertIn("if node requires both outcomes", validate_data(example))

    def test_unary_boolean_condition_requires_single_value_metadata(self):
        example = copy.deepcopy(self.sample)
        condition = next(node for node in example["nodes"] if node["type"] == "n8n-nodes-base.if")
        condition["parameters"]["conditions"]["conditions"][0]["operator"].pop("singleValue", None)
        self.assertIn("unary boolean condition requires singleValue", validate_data(example))

    def test_email_is_rejected(self):
        example = copy.deepcopy(self.sample)
        example["description"] = "contact@example.invalid"
        self.assertIn("external address or email", validate_data(example))


if __name__ == "__main__":
    unittest.main()
