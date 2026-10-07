## Change

Describe the behavior and reason for the change.

## Verification

- [ ] `python scripts/validate_examples.py`
- [ ] `python scripts/build_retrieval_example.py --check`
- [ ] `python -m unittest discover -s tests -v`
- [ ] `node --test tests/tenant_retrieval.test.mjs`
- [ ] Manual import/run in an isolated n8n instance, or explain why it was not run
- [ ] All sample data is synthetic; no client name, identifier, credential, external address, or operational export is included
- [ ] No Agent node, authored prompt, or pinned execution data is included
